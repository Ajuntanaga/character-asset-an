"""Package allowlisted inputs for one authorized, private GPU trial."""
import argparse
import ast
import base64
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
import time
import urllib.error
import urllib.request
import urllib.parse
import zipfile


root = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('--revision', default='V583')
args = parser.parse_args()
revision = args.revision.upper()
assert revision.startswith('V') and revision[1:].isdigit(), revision
staging = root / 'kaggle_payload' / revision.lower()
dataset = staging / 'input'
kernel = staging / 'kernel'
dataset.mkdir(parents=True, exist_ok=True)
kernel.mkdir(parents=True, exist_ok=True)
staging.chmod(0o700)
assert not (dataset / 'current-v544.blend').exists(), 'Do not upload the full scene locally'
assets = [
    'assets/generated/gray_maple_v553/gray_curly_maple_albedo.png',
    'assets/generated/gray_maple_v553/SOURCE.json',
    'references/derived/photoreal_facebuilder_v1/character_an_front_v1.png',
    'references/derived/photoreal_facebuilder_v1/fitted_cameras_v326.json',
    'github_assets/v567-rear-collar-mask.json',
    'github_assets/v568-pen-cloth-mask.json',
    'github_assets/v578-collar-rim-mask.json',
    'github_assets/antonia-hand/arms_albedo.png',
    'github_assets/antonia-hand/arms_bump.png',
    'github_assets/antonia-hand/arms_gloss.png',
    'github_assets/antonia-hand/SOURCE.json',
    'licenses/Antonia.txt',
]
inputs_manifest = json.dumps({'format': 1, 'files': {
    name: {'bytes': (root / name).stat().st_size,
           'sha256': hashlib.sha256((root / name).read_bytes()).hexdigest()}
    for name in assets
}}, sort_keys=True, separators=(',', ':')).encode()
inputs_manifest_hash = hashlib.sha256(inputs_manifest).hexdigest()
archive = dataset / 'reference-inputs.zip'
with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=1) as bundle:
    for name in assets:
        bundle.write(root / name, name)
    bundle.writestr('reference-inputs-manifest.json', inputs_manifest)
archive_hash = hashlib.sha256(archive.read_bytes()).hexdigest()
sources, pending = {}, ['github_scene_job', 'kaggle_reference_inputs']
while pending:
    name = pending.pop()
    relative = 'pipeline/' + name + '.py'
    path = root / relative
    if relative in sources or not path.is_file():
        continue
    source = path.read_text()
    sources[relative] = source
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.ImportFrom) and node.module:
            pending.append(node.module.split('.')[0])
        elif isinstance(node, ast.Import):
            pending.extend(alias.name.split('.')[0] for alias in node.names)
encoded = base64.b64encode(gzip.compress(json.dumps(sources, sort_keys=True).encode(), mtime=0)).decode()


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, response, code, message, headers, new_url):
        return None


# Only expiring, single-asset URLs enter the ignored private kernel. The
# GitHub credential remains in this process and never enters the bundle.
token = subprocess.check_output(['gh', 'auth', 'token'], text=True).strip()
opener = urllib.request.build_opener(NoRedirect)
manifest = json.loads((root / 'github_assets/scene-manifest.json').read_text())
downloads = []
for version, name in [('528', 'current-v528.blend'),
                      ('543', 'current-v543.delta.zst'),
                      ('544', 'current-v544.delta.zst')]:
    release = json.loads(subprocess.check_output([
        'gh', 'api', f'repos/Ajuntanaga/character-asset-an/releases/tags/checkpoint-v{version}']))
    asset = next(asset for asset in release['assets'] if asset['name'] == name)
    for attempt in range(6):
        request = urllib.request.Request(asset['url'] + f'?fresh={time.time_ns()}', headers={
            'Cache-Control': 'no-cache', 'Authorization': 'Bearer ' + token, 'Accept': 'application/octet-stream',
            'X-GitHub-Api-Version': '2022-11-28', 'User-Agent': 'Character-An-private-render'})
        try:
            response = opener.open(request, timeout=30)
            response.close()
            raise RuntimeError('Expected a temporary release-asset redirect')
        except urllib.error.HTTPError as error:
            if error.code != 302:
                raise RuntimeError(f'Asset redirect failed: HTTP {error.code}') from None
            url = error.headers['Location']
            assert url.startswith('https://release-assets.githubusercontent.com/')
        query = urllib.parse.parse_qs(urllib.parse.urlsplit(url).query)
        payload = query.get('jwt', [''])[0].split('.')
        assert len(payload) == 3, 'Missing release expiry token'
        expiry = json.loads(base64.urlsafe_b64decode(payload[1] + '==='))['exp']
        if expiry - time.time() >= 180:
            break
    else:
        raise RuntimeError(f'{name}: could not obtain a release URL valid for 3 minutes')
    downloads.append(dict(manifest[name], name=name, url=url))
del token
program = (f'REVISION = {revision!r}\nINPUTS_SHA256 = {archive_hash!r}\n'
           f'INPUTS_MANIFEST_SHA256 = {inputs_manifest_hash!r}\nSOURCES_B64 = {encoded!r}\n'
           f'SCENE_DOWNLOADS = {downloads!r}\nSCENE_MANIFEST = {manifest!r}\n' +
           (root / 'pipeline/kaggle_character_job.py').read_text())
ast.parse(program)
(kernel / 'character_job.py').write_text(program)
(kernel / 'character_job.py').chmod(0o600)
(dataset / 'dataset-metadata.json').write_text(json.dumps({
    'id': 'anthovargas/character-an-v544-render-inputs',
    'title': 'Character An V544 Render Inputs',
    'licenses': [{'name': 'other'}],
    'description': 'Private working inputs for one bounded character render. Copyright remains with the original authors. No redistribution license is granted; not a public asset release.',
}, indent=2))
(kernel / 'kernel-metadata.json').write_text(json.dumps({
    'id': f'anthovargas/character-an-{revision.lower()}-gpu-preview',
    'title': f'Character An {revision} GPU Preview',
    'code_file': 'character_job.py', 'language': 'python', 'kernel_type': 'script',
    'is_private': True, 'enable_gpu': True, 'enable_internet': True,
    'machine_shape': 'NvidiaTeslaT4',
    'dataset_sources': ['anthovargas/character-an-v544-render-inputs'],
}, indent=2))
print(json.dumps({'dataset': str(dataset), 'kernel': str(kernel),
                  'upload_bytes': archive.stat().st_size + len(program.encode()),
                  'new_local_bytes': archive.stat().st_size + len(program.encode()),
                  'script_count': len(sources), 'archive_sha256': archive_hash}, indent=2))
