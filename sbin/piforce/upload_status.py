"""State for one ordinary WiPi upload; only the loader writes these files."""
import fcntl
import hashlib
import json
import os
import tempfile
import time
import uuid

RUNTIME_DIR = '/run/wipi'


class UploadBusy(Exception):
    pass


def process_start(pid):
    with open('/proc/{}/stat'.format(pid)) as source:
        return source.read().rsplit(')', 1)[1].split()[19]


def file_hash(path):
    try:
        with open(path, 'rb') as source:
            return hashlib.sha256(source.read()).hexdigest()
    except FileNotFoundError:
        return None


class UploadStatus:
    def __init__(self, target, rom):
        os.makedirs(RUNTIME_DIR, mode=0o755, exist_ok=True)
        prefix = os.path.join(RUNTIME_DIR, 'upload-' + hashlib.sha256(target.encode('utf-8')).hexdigest())
        self.lock = open(prefix + '.lock', 'a')
        try:
            fcntl.flock(self.lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            self.lock.close()
            raise UploadBusy()
        self.path = prefix + '.json'
        progress_path = '/var/log/progress_' + target
        baseline_hash = file_hash(progress_path)
        try:
            baseline_mtime = int(os.stat(progress_path).st_mtime)
        except FileNotFoundError:
            baseline_mtime = None
        self.state = {
            'version': 1, 'id': uuid.uuid4().hex, 'target': target, 'rom': rom,
            'pid': os.getpid(), 'process_start': process_start(os.getpid()),
            'started': time.time(), 'state': 'active',
            'progress_baseline': baseline_hash, 'progress_baseline_mtime': baseline_mtime,
        }
        try:
            self.save()
        except BaseException:
            self.lock.close()
            raise

    def save(self):
        self.state['updated'] = time.time()
        name = None
        try:
            with tempfile.NamedTemporaryFile(mode='w', dir=RUNTIME_DIR, delete=False) as output:
                name = output.name
                json.dump(self.state, output)
                output.flush()
                os.fchmod(output.fileno(), 0o644)
                os.fsync(output.fileno())
            os.replace(name, self.path)
            name = None
        finally:
            if name is not None:
                os.unlink(name)

    def finish(self, success, detail=''):
        self.state['state'] = 'complete' if success else 'error'
        self.state['detail'] = detail[-2000:]
        self.save()

    def close(self):
        try:
            if self.state['state'] == 'active':
                self.finish(False, 'The upload was interrupted before completion.')
        finally:
            self.lock.close()


def sender_error(result, target, rom):
    if result.stderr.strip():
        return result.stderr.strip()[-2000:]
    # The legacy sender has one shared log. Show it only if it identifies this upload.
    try:
        with open('/var/log/netdimm_send.log', 'rb') as source:
            identity = source.read(2048).decode('utf-8', errors='replace')
            if rom in identity and target in identity:
                source.seek(0, os.SEEK_END)
                size = source.tell()
                source.seek(max(0, size - 2000))
                return source.read().decode('utf-8', errors='replace').strip()
    except OSError:
        pass
    return 'The game sender exited with status {}.'.format(result.returncode)
