"""Prepare a private render-only job from a verified Actions scene delta."""
import argparse
import ast
import base64
import gzip
import hashlib
import json
import os
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('artifact', type=Path)
parser.add_argument('--previous-payload', type=Path, required=True)
parser.add_argument('--revision', required=True)
args = parser.parse_args()
root = Path(__file__).resolve().parents[1]
revision = args.revision.lower()
assert revision.isalnum()
manifest_path, = args.artifact.rglob('build-manifest.json')
manifest = json.loads(manifest_path.read_text())
delta_name, = [name for name in manifest if name.endswith('.delta.zst')]
output_name, = [name for name in manifest if name.endswith('.blend') and name != 'current-v544.blend']
delta, = args.artifact.rglob(delta_name)
with delta.open('rb') as stream:
    assert hashlib.file_digest(stream, 'sha256').hexdigest() == manifest[delta_name]['sha256']
assert delta.stat().st_size == manifest[delta_name]['bytes']
constants = {}
needed = {'SCENE_DATASET', 'INPUTS_SHA256', 'INPUTS_MANIFEST_SHA256', 'SCENE_MANIFEST'}
for node in ast.parse(args.previous_payload.read_text()).body:
    if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name) and node.targets[0].id in needed:
        constants[node.targets[0].id] = ast.literal_eval(node.value)
assert constants.keys() == needed and constants['SCENE_DATASET'] is True
assert manifest['current-v544.blend']['sha256'] == constants['SCENE_MANIFEST']['current-v544.blend']['sha256']
folder = root / 'kaggle_payload' / revision
kernel, dataset = folder / 'kernel', folder / 'dataset'
kernel.mkdir(parents=True, exist_ok=False)
dataset.mkdir()
os.link(delta, dataset / delta_name)
dataset_id = f'anthovargas/character-an-{revision}-built-scene'
(dataset / 'dataset-metadata.json').write_text(json.dumps({
    'id': dataset_id, 'title': f'Character An {revision.upper()} Built Scene',
    'licenses': [{'name': 'other'}],
    'description': 'Private working scene delta. Original asset rights retained; no redistribution license.',
}, indent=2))
constants.update(REVISION=revision.upper() + '_SAVED_SCENE_RENDER', SCENE_DOWNLOADS=[],
    BUILT_SCENE_DELTA={'name': delta_name, 'sha256': manifest[delta_name]['sha256'],
        'base_sha256': manifest['current-v544.blend']['sha256'],
        'output_sha256': manifest[output_name]['sha256']})
sources = {'pipeline/' + name: (root / 'pipeline' / name).read_text()
           for name in ('github_scene_job.py', 'kaggle_reference_inputs.py')}
for name, source in sources.items():
    compile(source, name, 'exec')
constants['SOURCES_B64'] = base64.b64encode(gzip.compress(json.dumps(sources).encode(), mtime=0)).decode()
program = ''.join(f'{name} = {value!r}\n' for name, value in constants.items())
program += (root / 'pipeline/kaggle_character_job.py').read_text()
compile(program, 'character_job.py', 'exec')
(kernel / 'character_job.py').write_text(program)
(kernel / 'character_job.py').chmod(0o600)
(kernel / 'kernel-metadata.json').write_text(json.dumps({
    'id': f'anthovargas/character-an-{revision}-saved-scene-render',
    'title': f'Character An {revision.upper()} Saved Scene Render',
    'code_file': 'character_job.py', 'language': 'python', 'kernel_type': 'script',
    'is_private': True, 'enable_gpu': True, 'enable_internet': True,
    'machine_shape': 'NvidiaTeslaT4',
    'dataset_sources': ['anthovargas/character-an-v544-durable-inputs', dataset_id],
}, indent=2))
print(json.dumps({'kernel': str(kernel), 'dataset': str(dataset), 'delta_bytes': delta.stat().st_size}))
