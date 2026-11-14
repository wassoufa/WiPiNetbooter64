"""Validate the experimental menu artifact using the installed Naomi ROM library."""
import datetime
import hashlib
import json
from pathlib import Path
import sys

from naomi import NaomiRom


def require(condition, message):
    if not condition:
        raise ValueError(message)


path = Path(sys.argv[1])
data = path.read_bytes()
rom = NaomiRom(data)
require(rom.valid, 'Invalid Naomi header')
require(rom.serial == b'BRP0', 'Unexpected menu serial')
require(rom.date == datetime.date(2026, 11, 13), 'Unexpected baseline date')
require(rom.main_executable.entrypoint == 0x0C021000, 'Unexpected main entry point')
require(rom.test_executable.entrypoint == 0x0C021004, 'Unexpected test entry point')
for executable in [rom.main_executable, rom.test_executable]:
    require(executable.sections, 'Executable has no sections')
    for section in executable.sections:
        require(section.offset >= 0x500 and section.length > 0, 'Invalid executable section')
        require(section.offset + section.length <= len(data), 'Truncated executable section')
        require(0x0C000000 <= section.load_address < 0x0D000000, 'Invalid section load address')
        require(section.load_address + section.length <= 0x0D000000, 'Executable overlaps host configuration')

source = Path(__file__).resolve().parent / 'netbootmenu'
manifest = {
    'artifact': path.name, 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest(),
    'serial': rom.serial.decode(), 'date': str(rom.date),
    'main_entrypoint': hex(rom.main_executable.entrypoint),
    'test_entrypoint': hex(rom.test_executable.entrypoint),
    'renderer_source': 'hmofet/netboot@6ccbfdd000e705678ee422ebe972c2fccce40693',
    'libnaomi': 'DragonMinded/libnaomi@c840eb85384725182392ee3361706e80ae4ca4c0',
    'source_sha256': {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                      for p in sorted(source.iterdir()) if p.is_file()},
    'hardware_acceptance': 'pending', 'deployed': False,
}
print(json.dumps(manifest, indent=2))
