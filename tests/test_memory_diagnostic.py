import importlib.util
import os
from pathlib import Path
import shutil
import shlex
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('decoder', ROOT / 'native/diagnostics/decode-memory.py')
decoder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(decoder)


class MemoryDiagnosticTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        path = Path(cls.temp.name)
        (path / 'naomi/message').mkdir(parents=True)
        (path / 'malloc.h').write_text('#pragma once\n#include <stdint.h>\nstruct mallinfo { uint32_t arena, uordblks, fordblks; };\nstruct mallinfo mallinfo(void);\n')
        (path / 'naomi/ta.h').write_text('#include <malloc.h>\nstruct mallinfo ta_texture_mallinfo(void);\n')
        (path / 'naomi/timer.h').write_text('#include <stdint.h>\nint timer_start(uint32_t);\nuint32_t timer_elapsed(int);\nvoid timer_stop(int);\n')
        (path / 'naomi/message/message.h').write_text('#include <stdint.h>\nint message_send(uint16_t, void *, unsigned int);\n')
        (path / 'naomi/message/packet.h').write_text('''#pragma once
typedef struct { unsigned int packets_sent, packets_received, packets_cancelled, checksum_errors,
packets_pending_send, packets_pending_receive, send_in_progress, receive_in_progress; } packetlib_stats_t;
packetlib_stats_t packetlib_stats(void);
''')
        cls.program = path / 'sampler'
        subprocess.run([shutil.which('cc') or 'cc', '-std=c11', '-Wall', '-Wextra', '-Werror',
                        *shlex.split(os.environ.get('NATIVE_TEST_CFLAGS', '')),
                        '-I' + str(path), '-I' + str(ROOT / 'native/diagnostics'),
                        str(ROOT / 'tests/fixtures/native_memory_diagnostic_test.c'), '-o', str(cls.program)], check=True)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def run_sampler(self, case):
        return subprocess.check_output([str(self.program), case], text=True)

    def test_sampler_and_capture(self):
        capture = self.run_sampler('normal')
        rows = decoder.decode(capture, 1, 1)
        self.assertEqual([row['event'] for row in rows], [1, 2, 3, 4])
        prefixed = ''.join('2026-11-14 00:00:00,000 ' + line for line in capture.splitlines(keepends=True))
        self.assertEqual(decoder.decode(prefixed, 1, 1), rows)
        for bad in (capture[:-1], capture.replace('B4M1,2,', 'B4M1,1,'),
                    capture.replace('B4M1,2,', 'B4M1,9,'), capture.replace(',3,0,7,', ',3,0,8,'),
                    '\n'.join(capture.splitlines()[:2]) + '\n', capture.replace('B4M1', 'B4M2')):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                decoder.decode(bad, 1, 1)

    def test_failures_are_unusable(self):
        for case in ('allocation-failure', 'bad-heap', 'no-texture', 'send-failure', 'clock-failure', 'clock-wrap', 'calibration-race', 'save-route'):
            with self.subTest(case=case), self.assertRaises(ValueError):
                decoder.decode(self.run_sampler(case), 1, 1)

    def test_bounded_overflow_is_not_completion(self):
        capture = self.run_sampler('overflow')
        self.assertLessEqual(len(capture.splitlines()), 96)
        with self.assertRaises(ValueError):
            decoder.decode(capture, 0, 1)

    def test_declared_idle_and_same_game_scope(self):
        rows = decoder.decode(self.run_sampler('normal'), 1, 1)

        def capture(items):
            return ''.join('B4M1,' + ','.join(str(dict(row, sequence=i + 1)[field]) for field in decoder.FIELDS) + '\n'
                           for i, row in enumerate(items))

        # An idle sample before settings cannot satisfy the final idle block.
        before = [rows[0], dict(rows[3], cycle=0, guest_us=70000000),
                  dict(rows[1], guest_us=80000000), dict(rows[2], guest_us=90000000)]
        with self.assertRaises(ValueError):
            decoder.decode(capture(before), 1, 1)
        too_close = [*rows[:3], dict(rows[3], guest_us=rows[2]['guest_us'] + 1)]
        with self.assertRaises(ValueError):
            decoder.decode(capture(too_close), 1, 1)
        changed = [*rows[:3], dict(rows[1], cycle=1, game=8, guest_us=80000000),
                   dict(rows[2], cycle=2, game=8, guest_us=90000000)]
        with self.assertRaises(ValueError):
            decoder.decode(capture(changed), 2)


if __name__ == '__main__':
    unittest.main()
