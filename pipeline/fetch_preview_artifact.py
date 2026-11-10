import concurrent.futures
import io
import json
from pathlib import Path
import subprocess
import sys
import time
import zipfile
import requests

artifact, expected, destination = int(sys.argv[1]), int(sys.argv[2]), Path(sys.argv[3])
token = subprocess.check_output(['gh', 'auth', 'token'], text=True).strip()
r = requests.get(f'https://api.github.com/repos/Ajuntanaga/character-asset-an/actions/artifacts/{artifact}/zip', headers={'Authorization': 'Bearer '+token, 'Accept':'application/vnd.github+json'}, allow_redirects=False, timeout=30)
assert r.status_code == 302, f'Artifact redirect HTTP {r.status_code}'
url = r.headers['Location']
del token, r
chunk = 2 * 1024 * 1024

def fetch(start):
    end = min(expected, start+chunk)-1
    for attempt in range(3):
        try:
            response=requests.get(url, headers={'Range':f'bytes={start}-{end}'},timeout=(15,40))
            if response.status_code==206 and len(response.content)==end-start+1:
                return start,response.content
            if response.status_code==200 and len(response.content)==expected:
                return start,response.content[start:end+1]
            code=response.status_code
        except requests.RequestException:
            code='network timeout'
    raise RuntimeError(f'Chunk {start} failed: {code}')

with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
    parts=sorted(pool.map(fetch,range(0,expected,chunk)))
archive=b''.join(data for _,data in parts)
assert len(archive)==expected
with zipfile.ZipFile(io.BytesIO(archive)) as bundle:
    assert bundle.testzip() is None
    for item in bundle.infolist():
        path=Path(item.filename)
        assert not path.is_absolute() and '..' not in path.parts
    destination.mkdir(parents=True,exist_ok=True)
    bundle.extractall(destination)
print(json.dumps({'artifact':artifact,'bytes':len(archive),'crc_verified':True,'destination':str(destination)}))
