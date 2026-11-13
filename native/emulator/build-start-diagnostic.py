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
OUT = ROOT / 'native/out/start-diagnostic'

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
    header = '''/* LOCAL START DIAGNOSTIC ONLY: fixed scalar storage, guest milliseconds. */
#ifndef START_DIAGNOSTIC_H
#define START_DIAGNOSTIC_H
#include <stdint.h>
extern uint32_t sd_frame, sd_now, sd_gap, sd_maxgap, sd_press, sd_release;
extern uint32_t sd_elapsed, sd_bits, sd_eventbits, sd_route, sd_route_ms;
extern uint32_t sd_screen, sd_cursor, sd_press_frame, sd_release_frame;
extern uint32_t sd_poll, sd_raw, sd_selects, sd_uspf, sd_dec_us, sd_rel_us, sd_press_raw, sd_release_raw;
#endif
'''
    (menu / 'start-diagnostic.h').write_text(header)
    for name in ['main.c', 'screens.c', 'controls.c']:
        p = menu / name
        replace(p, '#include <stdint.h>' if name == 'main.c' else '#include "common.h"', ('#include <stdint.h>' if name == 'main.c' else '#include "common.h"') + '\n#include "start-diagnostic.h"')
    p = menu / 'main.c'
    replace(p, 'void main()', '''uint32_t sd_frame, sd_now, sd_gap, sd_maxgap, sd_press, sd_release;
uint32_t sd_elapsed, sd_bits, sd_eventbits, sd_route, sd_route_ms;
uint32_t sd_screen, sd_cursor, sd_press_frame, sd_release_frame;
uint32_t sd_poll, sd_raw, sd_selects, sd_uspf, sd_dec_us, sd_rel_us, sd_press_raw, sd_release_raw;

void main()''')
    replace(p, '        state.animation_counter = animation_counter;', '''        state.animation_counter = animation_counter;
        sd_frame++;
        uint32_t diagnostic_now = (uint32_t)(animation_counter * 1000.0);
        sd_gap = diagnostic_now - sd_now;
        if (sd_gap > sd_maxgap) sd_maxgap = sd_gap;
        sd_now = diagnostic_now;''')
    replace(p, '        // Display some debugging info.', '''        // Retained diagnostics on every screen, after TA rendering.
        video_draw_debug_text(8, 384, rgb(255, 255, 0), "DIAG guest ms F%u T%u gap%u max%u", sd_frame, sd_now, sd_gap, sd_maxgap);
        video_draw_debug_text(8, 396, rgb(255, 255, 0), "P%u F%u R%u F%u dt%u", sd_press, sd_press_frame, sd_release, sd_release_frame, sd_elapsed);
        video_draw_debug_text(8, 408, rgb(255, 255, 0), "bits%u event%u route%u at%u", sd_bits, sd_eventbits, sd_route, sd_route_ms);
        video_draw_debug_text(8, 420, rgb(255, 255, 0), "screen%u cursor%u (route 1=launch 2=settings)", sd_screen, sd_cursor);

        video_draw_debug_text(8, 432, rgb(255, 255, 0), "poll%u raw%u sends%u loop_us%u", sd_poll, sd_raw, sd_selects, sd_uspf);
        video_draw_debug_text(8, 444, rgb(255, 255, 0), "decision_us%u release_us%u raw P%u R%u", sd_dec_us, sd_rel_us, sd_press_raw, sd_release_raw);
        // Display some debugging info.''')
    replace(p, '        uint32_t uspf = profile_end(fps);', '        uint32_t uspf = profile_end(fps);\n        sd_uspf = uspf;')
    p = menu / 'controls.c'
    replace(p, '    return controls;', '''    static double diagnostic_press_time;
    sd_poll++;
    sd_raw = pressed.player1.start | (released.player1.start << 1) | (held.player1.start << 2) |
        (pressed.player2.start << 3) | (released.player2.start << 4) | (held.player2.start << 5);
    // Observe existing poll only: bits 0=pressed 1=released 2=held.
    sd_bits = controls.start_pressed | (controls.start_released << 1) |
        ((held.player1.start || (state->settings->system.players >= 2 && held.player2.start)) << 2);
    if (controls.start_pressed) {
        diagnostic_press_time = state->animation_counter;
        sd_press_raw = sd_raw; sd_dec_us = 0; sd_rel_us = 0; sd_release_raw = 0;
        sd_press = sd_now; sd_press_frame = sd_frame;
        sd_release = 0; sd_release_frame = 0; sd_elapsed = 0;
        sd_route = 0; sd_route_ms = 0; sd_eventbits = sd_bits;
    }
    if (controls.start_released) {
        sd_release_raw = sd_raw; sd_rel_us = (uint32_t)((state->animation_counter - diagnostic_press_time) * 1000000.0);
        sd_release = sd_now; sd_release_frame = sd_frame;
        sd_elapsed = sd_now - sd_press; sd_eventbits = sd_bits;
    }
    return controls;''')
    p = menu / 'screens.c'
    replace(p, '    switch(curscreen)', '    sd_screen = curscreen;\n    switch(curscreen)')
    replace(p, '                    // Made a selection!', '                    sd_dec_us = (uint32_t)((state->animation_counter - holding_animation) * 1000000.0); sd_selects++; sd_route = 1; sd_route_ms = sd_now; sd_elapsed = sd_now - sd_press;\n                    // Made a selection!')
    # Both existing settings assignments inside main_menu; no branch changes.
    text = p.read_text()
    a, b = text.split('unsigned int main_menu(state_t *state, int reinit)', 1)
    body, tail = b.split('unsigned int game_settings_load', 1)
    body = body.replace('controls_t controls = get_controls(state, reinit);', 'controls_t controls = get_controls(state, reinit);\n    sd_cursor = cursor;')
    anchor = 'new_screen = SCREEN_GAME_SETTINGS_LOAD;'
    if body.count(anchor) != 2:
        raise ValueError('Settings route anchors changed')
    body = body.replace(anchor, anchor + '\n                    if (sd_route != 2) { sd_dec_us = (uint32_t)((state->animation_counter - holding_animation) * 1000000.0); sd_route = 2; sd_route_ms = sd_now; sd_elapsed = sd_now - sd_press; }')
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
        subprocess.run(['docker', 'run', '--rm', '--platform', 'linux/amd64', '--network', 'none', '--read-only', '--tmpfs', '/tmp:exec', '-v', f'{ROOT}:/repo:ro', '-v', f'{OUT}:/repo/native/out/start-diagnostic', 'wipi-native-builder:baseline', 'python3', '-B', '/repo/native/emulator/build-start-diagnostic.py', '--container'], check=True)
        (OUT / 'builder-image-id.txt').write_bytes(subprocess.check_output(['docker', 'image', 'inspect', '--format', '{{.Id}}', 'wipi-native-builder:baseline']))
        print(OUT / 'configured-diagnostic.bin')
