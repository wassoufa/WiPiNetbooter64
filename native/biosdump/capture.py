#!/usr/bin/env python3
"""Capture-only client: never uploads, resets, restores, or selects a game."""
import argparse
import hashlib
import json
import math
import os
import signal
from pathlib import Path
import struct
import sys
import time

SIZE = 0x200000
CHUNK = 4096
READY, READ, DATA, DONE = range(0x2100, 0x2104)


def capture(receive, send, progress=None):
    """Strictly ordered exchange. Callbacks use (message id, bytes)."""
    if receive() != (READY, b''):
        raise ValueError('Expected empty BIOS helper READY; wrong helper or stale session')
    reads = []
    for pass_number in range(2):
        result = bytearray()
        for offset in range(0, SIZE, CHUNK):
            index = pass_number * (SIZE // CHUNK) + offset // CHUNK
            send(READ, struct.pack('<I', index))
            kind, data = receive()
            if kind != DATA or len(data) != CHUNK + 4 or struct.unpack('<I', data[:4])[0] != index:
                raise ValueError('Invalid chunk type, size, or sequence')
            result.extend(data[4:])
            if progress is not None and (offset // CHUNK + 1) % 64 == 0:
                progress(pass_number + 1, offset // CHUNK + 1, SIZE // CHUNK)
        reads.append(bytes(result))
    if receive() != (DONE, b''):
        raise ValueError('Missing empty completion marker')
    if reads[0] != reads[1]:
        raise ValueError('Independent BIOS reads differ; no accepted BIOS saved')
    return reads[0]


def private_output(path):
    """Reserve a new private directory before connecting; never overwrite evidence."""
    path = Path(path)
    path.mkdir(mode=0o700, parents=False, exist_ok=False)
    if path.is_symlink():
        raise ValueError('Symlink output directory')
    return path


def write_new(path, data):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'wb') as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('target', help='NetDIMM address; separately launched BIOS helper required')
    parser.add_argument('--output-dir', required=True, type=Path, help='New private directory under ignored native/out/runtime-tests')
    parser.add_argument('--connect', action='store_true', help='Explicitly connect to the already running helper (no upload/reset)')
    parser.add_argument('--timeout', type=float, default=1800, help='Hard capture deadline in seconds (Unix main process)')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    allowed = root / 'native/out/runtime-tests'
    output = args.output_dir.resolve()
    if not output.is_relative_to(allowed.resolve()) or output == allowed.resolve():
        parser.error('Output must be a new child directory under native/out/runtime-tests')
    if not math.isfinite(args.timeout) or args.timeout <= 0:
        parser.error('Timeout must be positive')
    if not args.connect:
        print('Dry run: capture two complete 2 MiB reads from a separately launched BIOS helper.')
        print('No connection, upload, reset, or output creation performed. Add --connect for capture.')
        return 0
    destination = private_output(output)
    sys.path.insert(0, str(root / 'sbin/piforce/dm_netboot'))
    from netdimm import NetDimm, Message, receive_message, send_message
    device = NetDimm(args.target)
    deadline = time.monotonic() + args.timeout
    def receive():
        while time.monotonic() < deadline:
            msg = receive_message(device)
            if msg is not None:
                return msg.id, msg.data
        raise TimeoutError('Capture deadline exceeded')
    def send(kind, data):
        if time.monotonic() >= deadline:
            raise TimeoutError('Capture deadline exceeded')
        send_message(device, Message(kind, data))
    def expired(signum, frame):
        raise TimeoutError('Hard capture deadline exceeded')
    previous = signal.signal(signal.SIGALRM, expired)
    try:
        signal.setitimer(signal.ITIMER_REAL, args.timeout)
        with device.connection():
            bios = capture(receive, send, lambda number, chunks, total:
                           print(f'BIOS read {number}/2: {chunks}/{total} chunks', flush=True))
    finally:
        if device.sock is not None:
            device.sock.close()
            device.sock = None
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)
    digest = hashlib.sha256(bios).hexdigest()
    write_new(destination / 'bios.bin', bios)
    write_new(destination / 'capture.json', (json.dumps({'bytes': len(bios), 'sha256': digest, 'complete_reads': 2, 'reads_equal': True}, indent=2) + '\n').encode())
    print(f'Accepted two equal complete reads: {len(bios)} bytes, SHA-256 {digest}')
    return 0

if __name__ == '__main__':
    sys.exit(main())
