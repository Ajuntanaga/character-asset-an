"""One private, bounded GPU preview job; prepended bundle is generated locally."""
import base64
import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import time
import urllib.request
import zipfile


started = time.monotonic()
budget_seconds = 1800
work = Path('/tmp/character-an')
work.mkdir(parents=True, exist_ok=True)
output = Path('/kaggle/working/results')
output.mkdir(parents=True, exist_ok=True)
status = {'status': 'STARTING', 'budget_seconds': budget_seconds,
          'revision': REVISION, 'maximum_selected_gpus': 1}


def remaining():
    left = budget_seconds - (time.monotonic() - started)
    if left <= 0:
        raise TimeoutError('Character preview budget exhausted')
    return left


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def download(url, target, expected_hash):
    with urllib.request.urlopen(url, timeout=min(90, remaining())) as response, target.open('wb') as stream:
        while block := response.read(1024 * 1024):
            remaining()
            stream.write(block)
    assert digest(target) == expected_hash, target.name


try:
    gpu = subprocess.check_output(
        ['nvidia-smi', '--query-gpu=name,memory.total,driver_version',
         '--format=csv,noheader'], text=True, timeout=min(30, remaining()))
    status['available_gpus'] = gpu.strip().splitlines()
    print(gpu, flush=True)
    candidates = list(Path('/kaggle/input').rglob('reference-inputs.zip'))
    assert len(candidates) == 1, candidates
    archive = candidates[0]
    assert digest(archive) == INPUTS_SHA256
    with zipfile.ZipFile(archive) as bundle:
        for entry in bundle.namelist():
            assert not Path(entry).is_absolute() and '..' not in Path(entry).parts
        bundle.extractall(work)
    scripts = json.loads(gzip.decompress(base64.b64decode(SOURCES_B64)))
    for name, source_text in scripts.items():
        target = work / name
        assert name.startswith('pipeline/') and len(Path(name).parts) == 2
        target.parent.mkdir(exist_ok=True)
        target.write_text(source_text)
    status['source_bundle_sha256'] = hashlib.sha256(SOURCES_B64.encode()).hexdigest()
    subprocess.run([sys.executable, '-m', 'pip', '-q', 'install', 'zstandard==0.25.0'],
                   check=True, timeout=min(120, remaining()))
    import zstandard
    for asset in SCENE_DOWNLOADS:
        downloaded = work / asset['name']
        download(asset['url'], downloaded, asset['sha256'])
        if 'base' in asset:
            dictionary = zstandard.ZstdCompressionDict((work / asset['base']).read_bytes(),
                                                       dict_type=zstandard.DICT_TYPE_RAWCONTENT)
            decoder = zstandard.ZstdDecompressor(dict_data=dictionary, max_window_size=1024 * 1024)
            restored = work / asset['output']
            with downloaded.open('rb') as source, restored.open('wb') as target:
                with decoder.stream_reader(source) as reader:
                    while block := reader.read(1024 * 1024):
                        remaining()
                        target.write(block)
            assert digest(restored) == SCENE_MANIFEST[asset['output']]['sha256']
            del decoder, dictionary
        print('Verified scene input:', asset['name'], flush=True)
    scene = work / 'current-v544.blend'
    tar_path = work / 'blender.tar.xz'
    url = 'https://ftp.nluug.nl/pub/graphics/blender/release/Blender5.2/blender-5.2.2-linux-x64.tar.xz'
    download(url, tar_path, '84098912789dc450e95697c4184fb8a90acbe5111c2ba4aede3fecb57806a168')
    with tarfile.open(tar_path) as archive:
        archive.extractall(work, filter='data')
    executable = work / 'blender-5.2.2-linux-x64/blender'
    command = [str(executable), '--background', '--disable-autoexec', str(scene),
               '--threads', '2', '--python-exit-code', '1', '--python',
               str(work / 'pipeline/github_scene_job.py'), '--',
               '--mode', 'combined-build', '--device', 'CUDA', '--output', str(output)]
    environment = dict(os.environ, OMP_NUM_THREADS='2', OPENBLAS_NUM_THREADS='2')
    status['status'] = 'RENDERING'
    with (output / 'blender.log').open('w') as log:
        subprocess.run(command, cwd=work, env=environment, stdout=log,
                       stderr=subprocess.STDOUT, check=True, timeout=remaining())
    status['status'] = 'SUCCEEDED_REQUIRES_VISUAL_REVIEW'
except Exception as error:
    status['status'] = 'FAILED'
    status['error'] = f'{type(error).__name__}: {error}'
    raise
finally:
    status['elapsed_seconds'] = round(time.monotonic() - started, 2)
    status['outputs'] = {p.name: {'bytes': p.stat().st_size, 'sha256': digest(p)}
                         for p in output.iterdir() if p.is_file()}
    (output / 'kaggle-job-report.json').write_text(json.dumps(status, indent=2))
    print(json.dumps(status), flush=True)
