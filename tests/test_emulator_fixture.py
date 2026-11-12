"""Offline fixture identity/layout checks; run in the existing native builder."""
import ast
import importlib.util
from pathlib import Path
import struct
from types import SimpleNamespace
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('emulator_fixture', ROOT / 'native/create-emulator-fixture.py')
fixture = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixture)


class EmulatorFixtureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base = (ROOT / 'native/out/netbootmenu.bin').read_bytes()

    def test_payload_matches_actual_host_serializer_and_native_layout(self):
        payload = fixture.make_payload()
        config, games = fixture.validate_payload(payload)
        tree = ast.parse((ROOT / 'sbin/piforce/dm_netboot/scripts/netdimm_menu.py').read_text())
        expression = next(node.value for node in ast.walk(tree)
                          if isinstance(node, ast.Assign)
                          and any(isinstance(t, ast.Name) and t.id == 'config' for t in node.targets)
                          and isinstance(node.value, ast.Call)
                          and isinstance(node.value.func, ast.Attribute)
                          and node.value.func.attr == 'pack')
        env = dict(struct=struct, SETTINGS_SIZE=64, games=games,
                   args=SimpleNamespace(debug_mode=False), last_game_id=0,
                   settings=SimpleNamespace(enable_analog=False, system_region=SimpleNamespace(value=2),
                                            use_filenames=False, disable_sound=True, sram_save=False,
                                            joy1_calibration=[128, 128, 0, 255, 0, 255],
                                            joy2_calibration=[128, 128, 0, 255, 0, 255]),
                   gamesconfig=payload[64:], fallback_data=None, force_players=2)
        host = eval(compile(ast.Expression(expression), '<actual host serializer>', 'eval'), env)
        self.assertEqual(payload[:64], host.ljust(64, b'\0'))
        self.assertEqual(config['game_list_offset'], 64)
        self.assertGreater(config['games_count'], (480 - 40) // 21)
        self.assertEqual(config['boot_selection'], games[0]['id'])
        self.assertEqual([g['id'] for g in games], list(range(len(games))))
        self.assertEqual(len(games[0]['name']), 1)
        self.assertEqual(len(games[-1]['name']), 127)
        for index, game in enumerate(games):
            start = 64 + index * 136
            self.assertEqual(payload[start:start + 128], game['name'].encode().ljust(128, b'\0'))
            self.assertEqual(payload[start + 128:start + 132], game['serial'].encode())
            self.assertEqual(struct.unpack_from('<I', payload, start + 132)[0], game['id'])
        self.assertEqual(start + 136, len(payload))

    def test_configured_rom_appends_one_section_without_changing_code(self):
        payload = fixture.make_payload()
        configured, rom = fixture.configure(self.base, payload)
        section = rom.main_executable.sections[-1]
        self.assertEqual((section.offset, section.length, section.load_address),
                         (len(self.base), len(payload), 0x0D000000))
        self.assertEqual(configured[section.offset:section.offset + section.length], payload)
        self.assertEqual(len(configured), section.offset + section.length)
        self.assertEqual(configured[rom.HEADER_LENGTH:section.offset], self.base[rom.HEADER_LENGTH:])
        self.assertNotEqual(fixture.sha256(configured), fixture.BASE_SHA256)
        with self.assertRaisesRegex(ValueError, 'identity mismatch'):
            fixture.configure(configured, payload)

    def test_malformed_and_wrong_base_rejected(self):
        for data in [b'', self.base[:0x500], self.base[:-1], self.base + b'\0',
                     bytes([self.base[0] ^ 1]) + self.base[1:],
                     self.base[:-1] + bytes([self.base[-1] ^ 1])]:
            with self.subTest(size=len(data)):
                with self.assertRaisesRegex(ValueError, 'identity mismatch'):
                    fixture.configure(data, fixture.make_payload())

    def test_truncation_count_pointer_id_and_name_mismatch_rejected(self):
        payload = fixture.make_payload()
        variants = [payload[:63], payload[:-1], payload + b'\0']
        for offset, value in [(0, 65), (4, 27), (16, 26), (32, 1),
                              (48, len(payload)), (52, 1), (64 + 132, 1)]:
            data = bytearray(payload)
            struct.pack_into('<I', data, offset, value)
            variants.append(bytes(data))
        for offset, value in [(64, ord('B')), (64 + 128, ord('Z')), (60, 1)]:
            data = bytearray(payload)
            data[offset] = value
            variants.append(bytes(data))
        variants.append(payload[:64] + b'X' * 128 + payload[64 + 128:])
        for data in variants:
            with self.subTest(sha256=fixture.sha256(data)):
                with self.assertRaises(ValueError):
                    fixture.validate_payload(data)


if __name__ == '__main__':
    unittest.main()
