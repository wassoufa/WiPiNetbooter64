"""Native menu wire/SRAM proof; compiles actual C code without hardware access."""
import ast
from pathlib import Path
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
        compiler = shutil.which('cc')
        if not compiler:
            raise RuntimeError('A host C compiler is required; run in the native builder container.')
        subprocess.run([
            compiler, '-std=c11', '-Wall', '-Wextra', '-Werror',
            '-I' + str(ROOT / 'tests/fixtures/native_include'),
            '-I' + str(ROOT / 'native/netbootmenu'),
            str(ROOT / 'tests/fixtures/native_menu_test.c'),
            str(ROOT / 'native/netbootmenu/config.c'),
            str(ROOT / 'native/netbootmenu/sram.c'), '-o', str(cls.binary),
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
        subprocess.run([str(self.binary), 'sram'], check=True)


if __name__ == '__main__':
    unittest.main()
