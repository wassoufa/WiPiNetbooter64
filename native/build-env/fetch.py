"""Fetch and verify the pinned source archives used by the isolated builder."""
import hashlib
import json
from pathlib import Path
import urllib.request

root = Path(__file__).resolve().parent
cache = root / '.cache'
cache.mkdir(exist_ok=True)
for item in json.loads((root / 'sources.json').read_text()):
    path = cache / item['name']
    if not path.exists():
        with urllib.request.urlopen(item['url'], timeout=60) as response:
            data = response.read()
        if hashlib.sha256(data).hexdigest() != item['sha256']:
            raise SystemExit('Checksum mismatch: ' + item['name'])
        path.write_bytes(data)
    if hashlib.sha256(path.read_bytes()).hexdigest() != item['sha256']:
        raise SystemExit('Cached checksum mismatch: ' + item['name'])
    print('Verified ' + item['name'])
