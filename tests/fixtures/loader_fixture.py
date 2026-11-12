"""Execute the actual loader with hardware imports and outbound commands replaced."""
import builtins,json,logging,os,sys,time,types,subprocess
from pathlib import Path
source=Path(sys.argv[1]).read_text();sandbox=Path(sys.argv[2]);target=sys.argv[3]
sys.path.insert(0,str(Path(sys.argv[1]).resolve().parent))
import upload_status
upload_status.RUNTIME_DIR=str(sandbox/'run/wipi')
original_open=builtins.open;original_makedirs=os.makedirs
for name in ['psutil','RPi','RPi.GPIO','netdimm']:
 sys.modules[name]=types.ModuleType(name)
sys.modules['netdimm'].NetDimm=object
sys.modules['RPi'].GPIO=sys.modules['RPi.GPIO']
def mapped(path):
 s=os.fspath(path)
 if s.startswith(('/sbin/piforce/','/var/www/html/','/var/log/','/run/wipi')):return str(sandbox/s.lstrip('/'))
 return path
def safe_open(path,*args,**kwargs):return original_open(mapped(path),*args,**kwargs)
def safe_makedirs(path,*args,**kwargs):return original_makedirs(mapped(path),*args,**kwargs)
def fake_system(cmd):
 if '/dm_netboot/netdimm_send ' in cmd or '/dm_netboot/netdimm_ensure ' in cmd:
  with original_open(sandbox/'events.jsonl','a')as fp:fp.write(json.dumps({'target':target,'pid':os.getpid()})+'\n')
  deadline=time.monotonic()+10
  while not (sandbox/'release').exists():
   if time.monotonic()>deadline:raise RuntimeError('Fixture not released')
   time.sleep(.02)
 return 0
def fake_run(args, **kwargs):
 if '/sbin/piforce/dm_netboot/netdimm_send' not in args:
  raise AssertionError('Unexpected outbound command: '+repr(args))
 fake_system('sudo python3 /sbin/piforce/dm_netboot/netdimm_send '+target)
 return subprocess.CompletedProcess(args, int(os.environ.get('WIPI_FIXTURE_EXIT', '0')), '', '')
subprocess.run=fake_run
builtins.open=safe_open;os.makedirs=safe_makedirs;os.system=fake_system
sys.argv=['wipiloader.py','test.bin.gz',target,'relayoff','hackoff','generic','none']
exec(compile(source,'actual-wipiloader.py','exec'),{'__name__':'__main__'})
