"""Native menu wire/SRAM/settings proof without hardware access."""
import ast
import os
from pathlib import Path
import shlex
import shutil
import struct
import subprocess
import tempfile
from types import SimpleNamespace
import unittest

ROOT = Path(__file__).resolve().parents[1]


class NativeMenuTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.binary = Path(cls.temp.name) / 'native-menu-test'
        cls.settings_binary = Path(cls.temp.name) / 'native-settings-test'
        cls.start_binary = Path(cls.temp.name) / 'native-start-test'
        compiler = shutil.which('cc')
        if not compiler:
            raise RuntimeError('A host C compiler is required; run in the native builder container.')
        flags = [compiler, '-std=c11', '-Wall', '-Wextra', '-Werror',
                 *shlex.split(os.environ.get('NATIVE_TEST_CFLAGS', ''))]
        includes = ['-I' + str(ROOT / 'tests/fixtures/native_include'),
                    '-I' + str(ROOT / 'native/netbootmenu')]
        subprocess.run([
            *flags,
            '-Dmalloc=native_test_malloc', '-Dfree=native_test_free',
            *includes,
            str(ROOT / 'tests/fixtures/native_menu_test.c'),
            str(ROOT / 'native/netbootmenu/config.c'),
            str(ROOT / 'native/netbootmenu/sram.c'), '-o', str(cls.binary),
        ], check=True)

        # Compile exact production regions with fake UI/message dependencies.
        # No copied parser or alternate implementation is maintained here.
        source_path = ROOT / 'native/netbootmenu/screens.c'
        source = source_path.read_text()
        regions = [('#define READ_ONLY_ALWAYS', 'void send_game_options('),
                   ('#define SCREEN_MAIN_MENU', '#define ERROR_BOX_WIDTH'),
                   ('unsigned int game_settings_load(', 'unsigned int game_settings(')]
        extracted = []
        for start, end in regions:
            offset = source.index(start)
            line = source.count('\n', 0, offset) + 1
            extracted.append(f'#line {line} "{source_path}"\n' +
                             source[offset:source.index(end, offset)])
        (Path(cls.temp.name) / 'native_settings_source.c').write_text('\n'.join(extracted))
        subprocess.run([
            *flags, '-Wno-sign-compare', *includes, '-I' + cls.temp.name,
            str(ROOT / 'tests/fixtures/native_settings_test.c'),
            '-o', str(cls.settings_binary),
        ], check=True)

        regions = [('static int selected_game =', 'static int expecting_boot ='),
                   ('static int sending_game_size =', 'static game_options_t *game_options ='),
                   ('#define SCREEN_MAIN_MENU', '#define ERROR_BOX_WIDTH'),
                   ('unsigned int main_menu(', 'unsigned int game_settings_load(')]
        extracted = []
        for start, end in regions:
            offset = source.index(start)
            line = source.count('\n', 0, offset) + 1
            extracted.append(f'#line {line} "{source_path}"\n' +
                             source[offset:source.index(end, offset)])
        (Path(cls.temp.name) / 'native_start_source.c').write_text('\n'.join(extracted))
        subprocess.run([
            *flags, '-Wno-sign-compare', *includes, '-I' + cls.temp.name,
            str(ROOT / 'tests/fixtures/native_start_test.c'),
            '-o', str(cls.start_binary),
        ], check=True)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_current_host_config_roundtrips_through_native_sender(self):
        # Extract the actual host's struct.pack expression, not a duplicate format.
        tree = ast.parse((ROOT / 'sbin/piforce/dm_netboot/scripts/netdimm_menu.py').read_text())
        expression = next(node.value for node in ast.walk(tree)
                          if isinstance(node, ast.Assign)
                          and any(isinstance(t, ast.Name) and t.id == 'config' for t in node.targets)
                          and isinstance(node.value, ast.Call)
                          and isinstance(node.value.func, ast.Attribute)
                          and node.value.func.attr == 'pack')
        for sram_enabled in [False, True]:
            settings = SimpleNamespace(enable_analog=True, system_region=SimpleNamespace(value=2),
                                       use_filenames=False, disable_sound=True, sram_save=sram_enabled,
                                       joy1_calibration=[128, 129, 1, 250, 2, 249],
                                       joy2_calibration=[126, 127, 3, 248, 4, 247])
            env = dict(struct=struct, SETTINGS_SIZE=64, games=[1, 2], args=SimpleNamespace(debug_mode=False),
                       last_game_id=1, settings=settings, gamesconfig=b'x' * 272,
                       fallback_data=b'font', force_players=2)
            payload = eval(compile(ast.Expression(expression), '<actual host serializer>', 'eval'), env)
            payload = payload.ljust(64, b'\0')
            result = subprocess.run([str(self.binary), 'config'], input=payload, capture_output=True, check=True)
            self.assertEqual(result.stdout, payload)
            self.assertEqual(struct.unpack_from('<I', result.stdout, 32)[0], int(sram_enabled))
            self.assertEqual(result.stdout[36:40], bytes([128, 129, 126, 127]))
            self.assertEqual(struct.unpack_from('<III', result.stdout, 48), (336, 4, 2))

    def test_sram_messages_with_fake_hardware_memory(self):
        result = subprocess.run([str(self.binary), 'sram'], capture_output=True, check=True)
        self.assertIn(b'1000 SRAM cycles, 7000 allocations released', result.stdout)

    def test_settings_parse_cleanup_and_caller_ownership(self):
        result = subprocess.run([str(self.settings_binary)], capture_output=True, check=True)
        self.assertIn(b'settings prefixes cleaned up; caller failure, mismatch and success ownership', result.stdout)
        self.assertIn(b'late response without ACK', result.stdout)

    def test_start_release_boundary_and_reinitialization(self):
        result = subprocess.run([str(self.start_binary)], capture_output=True, check=True)
        self.assertIn(b'Start release boundary, continuous hold, lock and reinit', result.stdout)


if __name__ == '__main__':
    unittest.main()
