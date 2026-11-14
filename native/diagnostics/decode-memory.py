#!/usr/bin/env python3
"""Validate bounded B4 stdout capture; this does not award soak acceptance."""
import argparse
import json
from pathlib import Path

FIELDS = ('sequence', 'cycle', 'event', 'screen', 'game', 'guest_us',
          'heap_valid', 'heap_arena', 'heap_used', 'heap_free',
          'texture_valid', 'texture_arena', 'texture_used', 'texture_free')


def decode(text, expected_cycles, minimum_idle=0):
    records = []
    opened = None
    chosen_game = None
    cycles = idle = 0
    last_time = 0
    for line in text.splitlines(keepends=True):
        if 'B4M' not in line:
            continue
        record = line[line.index('B4M'):]
        parts = record.rstrip('\r\n').split(',')
        if (not line.endswith('\n') or len(record) > 256 or parts[0] != 'B4M1' or
                len(parts) != len(FIELDS) + 1 or
                any(not p.isascii() or not p.isdecimal() or len(p) > 20 for p in parts[1:])):
            raise ValueError('Malformed or truncated B4 record')
        row = dict(zip(FIELDS, map(int, parts[1:])))
        if len(records) >= 96 or row['sequence'] != len(records) + 1:
            raise ValueError('Missing, repeated, reordered or excess record')
        if row['guest_us'] <= last_time or row['guest_us'] > 0xFFFFFFFF:
            raise ValueError('Invalid guest time')
        last_time = row['guest_us']
        if row['event'] == 5:
            raise ValueError('Diagnostic record limit reached; capture is incomplete')
        if row['game'] > 0x7FFFFFFF:
            raise ValueError('Invalid selected game')
        for allocator in ('heap', 'texture'):
            arena, used, free = (row[allocator + '_' + field] for field in ('arena', 'used', 'free'))
            if row[allocator + '_valid'] != 1:
                raise ValueError(allocator + ' metric unavailable or calibration failed')
            if not 0 < arena <= 0xFFFFFFFF or not 0 <= used <= arena or not 0 <= free <= arena or used + free > arena:
                raise ValueError('Invalid ' + allocator + ' counters')
        event = row['event']
        if event == 1 and not records and row['cycle'] == 0 and row['screen'] == 0:
            pass
        elif event == 2 and records and opened is None and row['cycle'] == cycles and row['screen'] == 3:
            if chosen_game is not None and row['game'] != chosen_game:
                raise ValueError('Selected game changed between settings cycles')
            chosen_game = row['game']
            opened = row['game']
            idle = 0
        elif event == 3 and opened == row['game'] and row['cycle'] == cycles + 1 and row['screen'] == 0:
            cycles += 1
            opened = None
        elif event == 4 and records and opened is None and row['cycle'] == cycles and row['screen'] == 0:
            if chosen_game is not None and row['game'] != chosen_game:
                raise ValueError('Selected game changed during idle')
            if row['guest_us'] - records[-1]['guest_us'] < 60000000:
                raise ValueError('Idle record arrived before sparse guest interval')
            idle += 1
        else:
            raise ValueError('Missing or unexpected screen/cycle record')
        records.append(row)
    if not records or records[0]['event'] != 1 or opened is not None or cycles != expected_cycles or idle < minimum_idle:
        raise ValueError('Incomplete capture for declared cycles/idle samples')
    return records


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('capture', type=Path)
    parser.add_argument('--expect-cycles', type=int, required=True)
    parser.add_argument('--min-idle', type=int, default=0)
    args = parser.parse_args()
    if not 0 <= args.expect_cycles <= 46 or not 0 <= args.min_idle <= 94:
        parser.error('Expected counts exceed bounded record policy')
    try:
        records = decode(args.capture.read_text(), args.expect_cycles, args.min_idle)
    except (OSError, ValueError) as error:
        parser.exit(1, str(error) + '\n')
    print(json.dumps({'records': records, 'guest_elapsed_us': records[-1]['guest_us'],
                      'host_elapsed': 'not established by guest records',
                      'acceptance': 'pending target evidence and trend review'}, indent=2))
