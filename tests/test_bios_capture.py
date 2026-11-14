import importlib.util
from pathlib import Path
import struct
import tempfile
import unittest
import contextlib
import signal
import sys
import types
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('capture', Path(__file__).resolve().parents[1] / 'native/biosdump/capture.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

class CaptureTests(unittest.TestCase):
    def exchange(self, corrupt=None):
        self.pending = (m.READY, b'')
        self.requests = []
        def receive():
            packet = self.pending
            self.pending = (m.DONE, b'')
            return packet
        def send(kind, data):
            self.assertEqual(kind, m.READ)
            index, = struct.unpack('<I', data)
            self.requests.append(index)
            payload = data + bytes([index % 256]) * m.CHUNK
            packet = (m.DATA, payload)
            self.pending = corrupt(index, packet) if corrupt else packet
        return receive, send

    def test_two_complete_independent_passes(self):
        progress = []
        result = m.capture(*self.exchange(), progress=lambda *values: progress.append(values))
        self.assertEqual(progress, [(number, chunks, 512) for number in (1, 2) for chunks in range(64, 513, 64)])
        self.assertEqual(len(result), m.SIZE)
        self.assertEqual(self.requests, list(range(2 * m.SIZE // m.CHUNK)))

    def test_truncation_wrong_type_and_out_of_range_sequence(self):
        for change in (lambda p: (p[0], p[1][:-1]), lambda p: (m.READY, p[1]), lambda p: (p[0], struct.pack('<I', 0xffffffff) + p[1][4:])):
            with self.subTest(change=change), self.assertRaises(ValueError):
                m.capture(*self.exchange(lambda i, p: change(p) if i == 1 else p))

    def test_second_physical_read_mismatch(self):
        with self.assertRaisesRegex(ValueError, 'differ'):
            m.capture(*self.exchange(lambda i, p: (p[0], p[1][:-1] + b'x') if i == 512 else p))

    def test_completion_and_ready_required(self):
        with self.assertRaises(ValueError):
            m.capture(lambda: (m.DATA, b''), lambda *args: None)
        receive, send = self.exchange()
        count = 0
        def incomplete():
            nonlocal count
            count += 1
            return (m.DATA, b'') if count == 1026 else receive()
        with self.assertRaises(ValueError):
            m.capture(incomplete, send)

    def test_hard_deadline_closes_failed_connect_socket(self):
        class Socket:
            closed = False
            def close(self):
                self.closed = True
        sock = Socket()
        class Device:
            def __init__(self, target):
                self.sock = sock
            @contextlib.contextmanager
            def connection(self):
                # Simulate the legacy connect path before its cleanup is active.
                while True:
                    pass
                yield
        fake = types.SimpleNamespace(NetDimm=Device, Message=object,
                                     receive_message=lambda *a: None,
                                     send_message=lambda *a: None)
        root = Path(m.__file__).resolve().parents[2]
        parent = root / 'native/out/runtime-tests'
        parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=parent) as temporary:
            argv = ['capture.py', 'example.invalid', '--connect', '--timeout', '0.02',
                    '--output-dir', str(Path(temporary) / 'capture')]
            previous = signal.getsignal(signal.SIGALRM)
            with patch.object(sys, 'argv', argv), patch.dict(sys.modules, {'netdimm': fake}):
                with self.assertRaisesRegex(TimeoutError, 'Hard'):
                    m.main()
            self.assertTrue(sock.closed)
            self.assertEqual(signal.getsignal(signal.SIGALRM), previous)
            self.assertEqual(signal.getitimer(signal.ITIMER_REAL)[0], 0)

    def test_private_new_output_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            output = m.private_output(Path(directory) / 'new')
            self.assertEqual(output.stat().st_mode & 0o777, 0o700)
            with self.assertRaises(FileExistsError):
                m.private_output(output)
            path = output / 'bios.bin'
            m.write_new(path, b'synthetic')
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)
            with self.assertRaises(FileExistsError):
                m.write_new(path, b'overwrite')
            link = output / 'link'
            link.symlink_to(path)
            with self.assertRaises(FileExistsError):
                m.write_new(link, b'overwrite')
            self.assertEqual(path.read_bytes(), b'synthetic')

if __name__ == '__main__':
    unittest.main()
