"""Run Kaggle CLI with bounded, resumable 2 MiB upload requests."""
from pathlib import Path
import requests
from kaggle.api.kaggle_api_extended import KaggleApi, ResumableUploadResult


def upload_complete(self, path, url, quiet, resume=False):
    size = Path(path).stat().st_size
    offset = 0
    failures = 0
    need_status = resume
    with open(path, 'rb') as source:
        while offset < size:
            try:
                if need_status:
                    response = requests.put(url, data=b'', headers={
                        'Content-Range': f'bytes */{size}', 'Content-Length': '0'},
                        timeout=(15, 30))
                    if response.status_code in (200, 201):
                        return ResumableUploadResult.COMPLETE
                    if response.status_code != 308:
                        print(f'Upload status HTTP {response.status_code}', flush=True)
                        return ResumableUploadResult.FAILED
                    accepted = response.headers.get('Range')
                    offset = int(accepted.rsplit('-', 1)[1]) + 1 if accepted else 0
                    need_status = False
                source.seek(offset)
                block = source.read(min(2 * 1024 * 1024, size - offset))
                end = offset + len(block) - 1
                response = requests.put(url, data=block, headers={
                    'Content-Range': f'bytes {offset}-{end}/{size}'}, timeout=(15, 40))
                if response.status_code in (200, 201):
                    assert end + 1 == size, 'Premature upload completion'
                    print(f'Uploaded {Path(path).name}: {size} bytes', flush=True)
                    return ResumableUploadResult.COMPLETE
                if response.status_code != 308:
                    raise RuntimeError(f'Upload HTTP {response.status_code}')
                accepted = response.headers.get('Range')
                next_offset = int(accepted.rsplit('-', 1)[1]) + 1 if accepted else 0
                if next_offset <= offset:
                    raise RuntimeError('Upload made no progress')
                offset = next_offset
                failures = 0
                if offset % (16 * 1024 * 1024) < len(block):
                    print(f'{Path(path).name}: {offset}/{size} bytes accepted', flush=True)
            except (requests.RequestException, RuntimeError):
                # Do not print signed upload URLs embedded in HTTP exceptions.
                failures += 1
                if failures >= 3:
                    print('Upload paused after three transport failures; checkpoint retained', flush=True)
                    return ResumableUploadResult.FAILED
                need_status = True
    return ResumableUploadResult.COMPLETE


if __name__ == '__main__':
    KaggleApi.upload_complete = upload_complete
    from kaggle.cli import main
    main()
