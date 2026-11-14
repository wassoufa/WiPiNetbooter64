#!/usr/bin/env python3
"""Offline diagnostic-only ROM. Run from the repository root with python3 -B.
Production sources and canonical ROM identity pins are never edited.
"""
import difflib
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'native/out/memory-diagnostic'

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def replace(path, old, new):
    text = path.read_text()
    if text.count(old) != 1:
        raise ValueError(f'Expected one patch anchor: {path}: {old!r}')
    path.write_text(text.replace(old, new))

def build():
    source = ROOT / 'native/netbootmenu'
    menu = Path('/tmp/memory-diagnostic-menu')
    shutil.copytree(source, menu)
    screen_source = (menu / 'screens.c').read_text().splitlines()
    for definition in ['#define SCREEN_MAIN_MENU 0', '#define SCREEN_GAME_SETTINGS 3']:
        if screen_source.count(definition) != 1:
            raise ValueError('Diagnostic screen IDs changed: ' + definition)
    for name in ['memory-diagnostic.c', 'memory-diagnostic.h']:
        shutil.copy2(ROOT / 'native/diagnostics' / name, menu / name)
    replace(menu / 'Makefile', 'SRCS += main.c', 'SRCS += main.c\nSRCS += memory-diagnostic.c')
    for name in ['main.c', 'screens.c', 'controls.c']:
        p = menu / name
        anchor = '#include <stdint.h>' if name == 'main.c' else '#include "common.h"'
        replace(p, anchor, anchor + '\n#include "memory-diagnostic.h"')
    replace(menu / 'main.c', '        animation_counter += (double)uspf / 1000000.0;',
            '        animation_counter += (double)uspf / 1000000.0;\n        md_frame();')
    replace(menu / 'screens.c', '    oldscreen = curscreen;',
            '    md_screen(curscreen, newscreen, selected_game);\n    oldscreen = curscreen;')
    p = menu / 'screens.c'
    text = p.read_text()
    before, body = text.split('unsigned int main_menu(state_t *state, int reinit)', 1)
    body, after = body.split('unsigned int game_settings_load', 1)
    if body.count('    return new_screen;') != 1:
        raise ValueError('Main-menu return anchor changed')
    body = body.replace('    return new_screen;', '    md_selection(cursor);\n    return new_screen;')
    p.write_text(before + 'unsigned int main_menu(state_t *state, int reinit)' + body + 'unsigned int game_settings_load' + after)
    replace(menu / 'controls.c', '    return controls;', '''    md_controls(held.player1.start || held.player2.start ||
        controls.start_pressed || controls.start_released || controls.test_pressed ||
        controls.service_pressed || controls.up_pressed || controls.down_pressed ||
        controls.left_pressed || controls.right_pressed);
    return controls;''')
    patches = []
    for name in ['Makefile', 'main.c', 'screens.c', 'controls.c', 'memory-diagnostic.c', 'memory-diagnostic.h']:
        old = (source / name).read_text() if (source / name).exists() else ''
        patches.extend(difflib.unified_diff(old.splitlines(True), (menu / name).read_text().splitlines(True), fromfile='a/' + name, tofile='b/' + name))
    (OUT / 'source.patch').write_text(''.join(patches))
    subprocess.run(['make', 'VENV_PYTHON3=/usr/bin/python3'], cwd=menu, check=True)
    shutil.copy2(menu / 'netbootmenu.bin', OUT / 'diagnostic-base.bin')
    shutil.copy2(menu / 'build/naomi.elf', OUT / 'diagnostic.elf')
    for filename, command in [('compiler.txt', ['/opt/toolchains/naomi/sh-elf/bin/sh-elf-gcc', '--version']), ('elf-header.txt', ['/opt/toolchains/naomi/sh-elf/bin/sh-elf-readelf', '-h', str(OUT / 'diagnostic.elf')])]:
        (OUT / filename).write_bytes(subprocess.check_output(command))
    shutil.copy2('/opt/toolchains/naomi/python-packages.txt', OUT / 'python-packages.txt')
    spec = importlib.util.spec_from_file_location('fixture', ROOT / 'native/create-emulator-fixture.py')
    fixture = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fixture)
    # Check canonical pin before reusing its payload; do NOT bypass/update validate_base.
    fixture.validate_base((ROOT / 'native/out/netbootmenu.bin').read_bytes())
    payload = fixture.make_payload()
    fixture.validate_payload(payload)
    base = (OUT / 'diagnostic-base.bin').read_bytes()
    from naomi import NaomiRom, add_or_update_section
    original = NaomiRom(base)
    result = add_or_update_section(base, fixture.CONFIG_ADDRESS, payload)
    rom = NaomiRom(result)
    assert [fixture.section_identity(s) for s in rom.main_executable.sections] == [fixture.section_identity(s) for s in original.main_executable.sections] + [(len(base), len(payload), fixture.CONFIG_ADDRESS)]
    assert result[rom.HEADER_LENGTH:len(base)] == base[rom.HEADER_LENGTH:]
    assert result[len(base):] == payload
    (OUT / 'configured-diagnostic.bin').write_bytes(result)
    (OUT / 'synthetic-config.bin').write_bytes(payload)
    manifest = {'purpose': 'OFFLINE B4 memory diagnostic readiness, no target acceptance or host bridge',
                'policy': {'settle_completed_frames': 120, 'idle_guest_us': 60000000, 'maximum_records': 96,
                           'events': {'1': 'main', '2': 'settings', '3': 'discard', '4': 'idle', '5': 'limit-unusable'},
                           'units': 'bytes and guest microseconds',
                           'heap': 'pinned newlib mallinfo: arena,uordblks,fordblks; one 4096-byte calibration',
                           'texture': 'pinned libnaomi ta_texture_mallinfo: arena,uordblks,fordblks'},
                'source_sha256': {str(p.relative_to(source)): digest(p) for p in sorted(source.rglob('*')) if p.is_file()},
                'instrumented_sha256': {name: digest(menu / name) for name in ['Makefile', 'main.c', 'screens.c', 'controls.c', 'memory-diagnostic.c', 'memory-diagnostic.h']},
                'recipe_sha256': digest(Path(__file__)), 'generator_sha256': digest(ROOT / 'native/create-emulator-fixture.py'),
                'decoder_sha256': digest(ROOT / 'native/diagnostics/decode-memory.py'),
                'files': {p.name: {'bytes': p.stat().st_size, 'sha256': digest(p)} for p in sorted(OUT.iterdir()) if p.is_file() and p.name != 'manifest.json'}}
    (OUT / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')

if __name__ == '__main__':
    if '--container' in sys.argv:
        build()
    else:
        OUT.mkdir(parents=True, exist_ok=True)
        (OUT / 'builder-image-id.txt').write_bytes(subprocess.check_output(['docker', 'image', 'inspect', '--format', '{{.Id}}', 'wipi-native-builder:baseline']))
        subprocess.run(['docker', 'run', '--rm', '--platform', 'linux/amd64', '--network', 'none', '--read-only', '--tmpfs', '/tmp:exec', '-v', f'{ROOT}:/repo:ro', '-v', f'{OUT}:/repo/native/out/memory-diagnostic', 'wipi-native-builder:baseline', 'python3', '-B', '/repo/native/emulator/build-memory-diagnostic.py', '--container'], check=True)
        print(OUT / 'configured-diagnostic.bin')
