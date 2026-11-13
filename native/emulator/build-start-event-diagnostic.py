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
OUT = ROOT / 'native/out/start-diagnostic-events'

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def replace(path, old, new):
    text = path.read_text()
    if text.count(old) != 1:
        raise ValueError(f'Expected one patch anchor: {path}: {old!r}')
    path.write_text(text.replace(old, new))

def build():
    source = ROOT / 'native/netbootmenu'
    menu = Path('/tmp/start-diagnostic-menu')
    shutil.copytree(source, menu)
    declarations = """uint32_t se_frame, se_press_frame, se_release_frame, se_press_raw, se_release_raw;
uint32_t se_route, se_sends, se_dec_us, se_rel_us, se_profile_ok;
uint64_t se_profile_us;
double se_press_time, se_release_time, se_dec_time;
"""
    header = '#ifndef START_EVENT_DIAGNOSTIC_H\n#define START_EVENT_DIAGNOSTIC_H\n#include <stdint.h>\n' + ''.join('extern ' + line + '\n' for line in declarations.splitlines()) + '#endif\n'
    (menu / 'start-diagnostic.h').write_text(header)
    for name in ['main.c', 'screens.c', 'controls.c']:
        p = menu / name
        anchor = '#include <stdint.h>' if name == 'main.c' else '#include "common.h"'
        replace(p, anchor, anchor + '\n#include "start-diagnostic.h"')
    p = menu / 'main.c'
    replace(p, 'void main()', declarations + '\nvoid main()')
    replace(p, '        state.animation_counter = animation_counter;', '        state.animation_counter = animation_counter;\n        se_frame++;')
    replace(p, '        // Display some debugging info.', '''        // No diagnostic draw or floating-point work before a route decision.
        if (se_route != 0) {
            video_draw_debug_text(8, 384, rgb(255, 255, 0), "EVENT route%u sends%u Pframe%u Rframe%u", se_route, se_sends, se_press_frame, se_release_frame);
            video_draw_debug_text(8, 396, rgb(255, 255, 0), "animation decision_us%u release_us%u", se_dec_us, se_rel_us);
            video_draw_debug_text(8, 408, rgb(255, 255, 0), "profile_valid%u elapsed_us%llu", se_profile_ok, (unsigned long long)se_profile_us);
            video_draw_debug_text(8, 420, rgb(255, 255, 0), "raw P%u R%u", se_press_raw, se_release_raw);
        }
        // Display some debugging info.''')
    p = menu / 'controls.c'
    replace(p, '    return controls;', '''    // Observe existing mapped events only. No extra input polls.
    static int event_profile = -1;
    if (controls.start_pressed) {
        if (event_profile >= 0) { profile_end(event_profile); event_profile = -1; }
        se_press_time = state->animation_counter;
        se_press_frame = se_frame; se_release_frame = 0;
        se_press_raw = pressed.player1.start | (released.player1.start << 1) | (held.player1.start << 2) |
            (pressed.player2.start << 3) | (released.player2.start << 4) | (held.player2.start << 5);
        se_release_raw = 0; se_route = 0; se_sends = 0;
        se_dec_us = 0; se_rel_us = 0; se_profile_ok = 0; se_profile_us = 0;
        event_profile = profile_start();
    }
    if (controls.start_released) {
        // Close the single event profiler before event conversion/draw overhead.
        if (event_profile >= 0) {
            se_profile_us = profile_end(event_profile); event_profile = -1; se_profile_ok = 1;
        }
        se_release_time = state->animation_counter;
        se_release_frame = se_frame;
        se_release_raw = pressed.player1.start | (released.player1.start << 1) | (held.player1.start << 2) |
            (pressed.player2.start << 3) | (released.player2.start << 4) | (held.player2.start << 5);
        if (se_press_frame != 0) se_rel_us = (uint32_t)((se_release_time - se_press_time) * 1000000.0);
    }
    return controls;''')
    p = menu / 'screens.c'
    replace(p, '                    // Made a selection!', '                    se_dec_time = state->animation_counter; se_dec_us = (uint32_t)((se_dec_time - holding_animation) * 1000000.0); se_sends++; se_route = 1;\n                    // Made a selection!')
    text = p.read_text()
    a, b = text.split('unsigned int main_menu(state_t *state, int reinit)', 1)
    body, tail = b.split('unsigned int game_settings_load', 1)
    anchor = 'new_screen = SCREEN_GAME_SETTINGS_LOAD;'
    if body.count(anchor) != 2:
        raise ValueError('Settings route anchors changed')
    body = body.replace(anchor, anchor + '\n                    if (se_route != 2) { se_dec_time = state->animation_counter; se_dec_us = (uint32_t)((se_dec_time - holding_animation) * 1000000.0); se_route = 2; }')
    p.write_text(a + 'unsigned int main_menu(state_t *state, int reinit)' + body + 'unsigned int game_settings_load' + tail)
    patches = []
    for name in ['main.c', 'screens.c', 'controls.c', 'start-diagnostic.h']:
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
    manifest = {'purpose': 'LOCAL Start timing diagnostic, no runtime acceptance or host bridge',
                'source_sha256': {str(p.relative_to(source)): digest(p) for p in sorted(source.rglob('*')) if p.is_file()},
                'instrumented_sha256': {name: digest(menu / name) for name in ['main.c', 'screens.c', 'controls.c', 'start-diagnostic.h']},
                'recipe_sha256': digest(Path(__file__)), 'generator_sha256': digest(ROOT / 'native/create-emulator-fixture.py'),
                'files': {p.name: {'bytes': p.stat().st_size, 'sha256': digest(p)} for p in sorted(OUT.iterdir()) if p.is_file() and p.name != 'manifest.json'}}
    (OUT / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')

if __name__ == '__main__':
    if '--container' in sys.argv:
        build()
    else:
        OUT.mkdir(parents=True, exist_ok=True)
        subprocess.run(['docker', 'run', '--rm', '--platform', 'linux/amd64', '--network', 'none', '--read-only', '--tmpfs', '/tmp:exec', '-v', f'{ROOT}:/repo:ro', '-v', f'{OUT}:/repo/native/out/start-diagnostic-events', 'wipi-native-builder:baseline', 'python3', '-B', '/repo/native/emulator/build-start-event-diagnostic.py', '--container'], check=True)
        (OUT / 'builder-image-id.txt').write_bytes(subprocess.check_output(['docker', 'image', 'inspect', '--format', '{{.Id}}', 'wipi-native-builder:baseline']))
        print(OUT / 'configured-diagnostic.bin')
