"""Restore pinned reference files from Kaggle's ZIP or expanded dataset mount."""
import hashlib
import json
from pathlib import Path
import zipfile


MANIFEST_NAME = 'reference-inputs-manifest.json'


def restore_reference_inputs(input_root, destination, archive_hash, manifest_hash):
    input_root, destination = Path(input_root), Path(destination)
    archives = list(input_root.rglob('reference-inputs.zip'))
    bundle = None
    try:
        if archives:
            assert len(archives) == 1, 'Ambiguous input archives'
            with archives[0].open('rb') as stream:
                assert hashlib.file_digest(stream, 'sha256').hexdigest() == archive_hash
            bundle = zipfile.ZipFile(archives[0])
            manifest_bytes = bundle.read(MANIFEST_NAME)
            source_root = None
        else:
            manifests = list(input_root.rglob(MANIFEST_NAME))
            assert len(manifests) == 1, 'Expected one expanded input manifest'
            manifest_bytes = manifests[0].read_bytes()
            source_root = manifests[0].parent.resolve()
        assert hashlib.sha256(manifest_bytes).hexdigest() == manifest_hash
        manifest = json.loads(manifest_bytes)
        assert manifest['format'] == 1 and manifest['files']
        restored = []
        for name, expected in manifest['files'].items():
            relative = Path(name)
            assert not relative.is_absolute() and '..' not in relative.parts
            if bundle:
                data = bundle.read(name)
            else:
                source = (source_root / relative).resolve()
                source.relative_to(source_root)
                data = source.read_bytes()
            assert len(data) == expected['bytes'], name
            assert hashlib.sha256(data).hexdigest() == expected['sha256'], name
            target = destination / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
            restored.append(name)
        return {'layout': 'zip' if bundle else 'expanded', 'files': restored}
    finally:
        if bundle:
            bundle.close()
