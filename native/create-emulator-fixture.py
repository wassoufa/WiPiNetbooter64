"""Build an offline, synthetic menu fixture; never import or run netdimm_menu.

Run inside the existing native builder (naomiutils supplies the ROM helper).
The pinned base is intentional: another build needs a reviewed identity update.
"""
import datetime
import hashlib
import json
from pathlib import Path
import struct

from naomi import NaomiRom, add_or_update_section

ROOT = Path(__file__).resolve().parents[1]
BASE_BYTES = 1461916
BASE_SHA256 = '45ef4f205449bb8cbae7ed74c8d064e6140de4b9ac4469b8c420c7941df1a035'
CONFIG_ADDRESS = 0x0D000000
CONFIG_SIZE = 64
GAME_SIZE = 136
# netdimm_menu.py's serializer plus the four reserved bytes in protocol.h.
CONFIG = struct.Struct('<IIIIIIIIIBBBBBBBBBBBBIII4x')
GAME = struct.Struct('<128s4sI')
CONFIG_FIELDS = (
    'game_list_offset games_count enable_analog enable_debug boot_selection '
    'system_region use_filenames disable_sound sram_save '
    'joy1_hcenter joy1_vcenter joy2_hcenter joy2_vcenter '
    'joy1_hmin joy1_hmax joy1_vmin joy1_vmax '
    'joy2_hmin joy2_hmax joy2_vmin joy2_vmax '
    'fallback_font_offset fallback_font_size force_players'
).split()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def synthetic_games():
    # More than the 20 visible rows at 640x480; include both name boundaries.
    titles = ['A', 'Amber Circuit', 'Blue Lantern', 'Cloud Orchard', 'Copper Kite',
              'Dawn Relay', 'Echo Harbor', 'Fern Valley', 'Glass Comet', 'Hidden Atlas',
              'Indigo Trail', 'Jade Balloon', 'Kestrel Bridge', 'Lunar Garden',
              'Marble Beacon', 'Northwind Picnic', 'Opal Meadow', 'Paper Rocket',
              'Quartz Parade', 'River Mosaic', 'Silver Acorn', 'Tangerine Summit',
              'Umbra Station', 'Velvet Compass', 'Willow Orbit',
              'Zephyr Expedition - ' + 'Long title navigation fixture ' * 4]
    return [dict(id=i, name=title[:127], serial=f'F{i:03d}')
            for i, title in enumerate(titles)]


def make_payload():
    games = synthetic_games()
    # Digital navigation, no overlay, first row, export region, muted sound,
    # SRAM off, centered/full-range calibration, no fallback font, two players.
    config = CONFIG.pack(CONFIG_SIZE, len(games), 0, 0, 0, 2, 0, 1, 0,
                         128, 128, 128, 128, 0, 255, 0, 255, 0, 255, 0, 255,
                         0, 0, 2)
    records = b''.join(GAME.pack(g['name'].encode('ascii'), g['serial'].encode('ascii'), g['id'])
                       for g in games)
    return config + records


def validate_payload(payload):
    require(CONFIG.size == CONFIG_SIZE and GAME.size == GAME_SIZE, 'Wire layout changed')
    require(len(payload) >= CONFIG_SIZE, 'Truncated configuration')
    config = dict(zip(CONFIG_FIELDS, CONFIG.unpack_from(payload)))
    require(config['game_list_offset'] == CONFIG_SIZE, 'Invalid game-list offset')
    require(config['games_count'] == len(synthetic_games()), 'Invalid game count')
    require(len(payload) == CONFIG_SIZE + config['games_count'] * GAME_SIZE,
            'Game records exceed payload or leave trailing data')
    require(config['boot_selection'] < config['games_count'], 'Selection out of range')
    require(payload[60:64] == bytes(4), 'Nonzero reserved configuration')
    require(config['sram_save'] == 0 and config['disable_sound'] == 1, 'Unsafe fixture flags')
    require(config['fallback_font_offset'] == config['fallback_font_size'] == 0,
            'Unexpected fallback font')
    games = []
    for index in range(config['games_count']):
        name, serial, game_id = GAME.unpack_from(payload, CONFIG_SIZE + index * GAME_SIZE)
        require(b'\0' in name, 'Unterminated game name')
        title, padding = name.split(b'\0', 1)
        require(not any(padding), 'Nonzero game-name padding')
        require(game_id == index, 'Game ID does not match list index')
        games.append(dict(id=game_id, name=title.decode('ascii'), serial=serial.decode('ascii')))
    require(games == synthetic_games(), 'Synthetic title/serial/ID mismatch')
    require(payload == make_payload(), 'Unexpected synthetic configuration value')
    return config, games


def section_identity(section):
    return (section.offset, section.length, section.load_address)


def validate_base(data):
    require(len(data) == BASE_BYTES and sha256(data) == BASE_SHA256,
            'Base ROM identity mismatch; rebuild/review the pinned baseline first')
    rom = NaomiRom(data)
    require(rom.valid and rom.serial == b'BRP0', 'Invalid baseline header/serial')
    require(rom.date == datetime.date(2026, 11, 13), 'Unexpected baseline date')
    for executable, entrypoint in [(rom.main_executable, 0x0C021000),
                                   (rom.test_executable, 0x0C021004)]:
        require(executable.entrypoint == entrypoint, 'Unexpected entrypoint')
        require(0 < len(executable.sections) < 8, 'No room for configuration section')
        for section in executable.sections:
            require(section.offset >= rom.HEADER_LENGTH and section.length > 0,
                    'Invalid executable section')
            require(section.offset + section.length <= len(data), 'Truncated executable section')
            require(0x0C000000 <= section.load_address < CONFIG_ADDRESS and
                    section.load_address + section.length <= CONFIG_ADDRESS,
                    'Executable overlaps configuration memory')
    return rom


def configure(base, payload):
    original = validate_base(base)
    validate_payload(payload)
    result = add_or_update_section(base, CONFIG_ADDRESS, payload)
    rom = NaomiRom(result)
    require(rom.valid, 'Invalid configured header')
    before = [section_identity(s) for s in original.main_executable.sections]
    after = [section_identity(s) for s in rom.main_executable.sections]
    require(after == before + [(len(base), len(payload), CONFIG_ADDRESS)],
            'Unexpected configured section layout')
    require(rom.main_executable.entrypoint == original.main_executable.entrypoint and
            rom.test_executable.entrypoint == original.test_executable.entrypoint and
            [section_identity(s) for s in rom.test_executable.sections] ==
            [section_identity(s) for s in original.test_executable.sections],
            'Existing executable changed')
    require(result[rom.HEADER_LENGTH:len(base)] == base[rom.HEADER_LENGTH:],
            'Original executable bytes changed')
    require(len(result) == len(base) + len(payload) and result[len(base):] == payload,
            'Appended configuration bounds/data mismatch')
    return result, rom


def main():
    base_path = ROOT / 'native/out/netbootmenu.bin'
    base = base_path.read_bytes()
    payload = make_payload()
    config, games = validate_payload(payload)
    result, rom = configure(base, payload)
    output = ROOT / 'native/out/emulator'
    manifest = {
        'purpose': 'Offline synthetic rendering/navigation fixture; no game ROMs or host bridge',
        'base': {'file': base_path.name, 'bytes': len(base), 'sha256': sha256(base)},
        'configuration': {'file': 'synthetic-config.bin', 'bytes': len(payload),
                          'sha256': sha256(payload), 'load_address': hex(CONFIG_ADDRESS),
                          'config_bytes': CONFIG_SIZE, 'game_record_bytes': GAME_SIZE,
                          'fields': config, 'games': games},
        'configured_rom': {'file': 'configured-menu.bin', 'bytes': len(result),
                           'sha256': sha256(result),
                           'main_sections': [dict(offset=s.offset, length=s.length,
                                                  load_address=hex(s.load_address))
                                             for s in rom.main_executable.sections]},
        'generator_sha256': sha256(Path(__file__).read_bytes()),
        'runtime_acceptance': 'not established by fixture generation', 'deployed': False,
    }
    files = {'configured-menu.bin': result, 'synthetic-config.bin': payload,
             'fixture-manifest.json': (json.dumps(manifest, indent=2) + '\n').encode()}
    output.mkdir(parents=True, exist_ok=True)
    for name, data in files.items():
        (output / name).write_bytes(data)
    (output / 'SHA256SUMS').write_text(''.join(f'{sha256(data)}  {name}\n'
                                               for name, data in files.items()))
    print(json.dumps({name: {'bytes': len(data), 'sha256': sha256(data)}
                      for name, data in files.items()}, indent=2))


if __name__ == '__main__':
    main()
