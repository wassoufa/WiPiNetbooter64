import json,subprocess,sys,tempfile,time,os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
fixture=Path(__file__).with_name('fixtures')/'loader_fixture.py'
new=ROOT/'sbin/piforce/wipiloader.py'
processes=[]
def setup(parent,name):
 p=parent/name;p.mkdir()
 for d in ['sbin/piforce','var/log','var/www/html/csv']:(p/d).mkdir(parents=True,exist_ok=True)
 for k,v in {'openmode':'openoff','ffbmode':'ffboff','emumode':'manual','hatserial':'hatserialoff','servermode':'serveroff','rpiversion':'4'}.items():(p/'sbin/piforce'/f'{k}.txt').write_text(v)
 return p
def start(code,p,target='10.0.0.3',exit_code=0):
 proc=subprocess.Popen([sys.executable,'-B',str(fixture),str(code),str(p),target],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,env=dict(os.environ,WIPI_FIXTURE_EXIT=str(exit_code)))
 processes.append(proc);return proc
def events(p):
 f=p/'events.jsonl'
 return [json.loads(l)for l in f.read_text().splitlines()]if f.exists()else[]
def wait_for(test):
 deadline=time.monotonic()+4
 while not test():
  if time.monotonic()>deadline:raise AssertionError('Condition timed out')
  time.sleep(.02)
def finish(proc):
 stdout,stderr=proc.communicate(timeout=4)
 assert proc.returncode==0,(proc.returncode,stdout,stderr)
results={}
try:
 with tempfile.TemporaryDirectory(prefix='upload-lock-',dir=ROOT/'tests')as tmp:
  root=Path(tmp)
  p=setup(root,'protected');a=start(new,p);wait_for(lambda:len(events(p))==1);b=start(new,p);c=start(new,p)
  finish(b);finish(c)
  assert a.poll()is None and len(events(p))==1
  log=(p/'var/log/wipiloader.log').read_text()
  assert 'Wipiloader script started' in log and log.count('Launch ignored: upload already in progress')==2
  (p/'release').touch();finish(a)
  results['protected_simultaneous_same_target_sends']=len(events(p))
  d=start(new,p);finish(d);assert len(events(p))==2
  results['later_explicit_launch_after_completion']='passed'
  results['duplicate_attempts_preserve_active_log']='passed'
  p=setup(root,'different-targets');a=start(new,p,'10.0.0.3');b=start(new,p,'10.0.0.4');wait_for(lambda:len(events(p))==2)
  assert {e['target']for e in events(p)}=={'10.0.0.3','10.0.0.4'}
  (p/'release').touch();finish(a);finish(b)
  results['separate_targets_remain_independent']='passed'
  p=setup(root,'failure-release');a=start(new,p);wait_for(lambda:len(events(p))==1);a.terminate();a.communicate(timeout=4)
  (p/'release').touch();b=start(new,p);finish(b);assert len(events(p))==2
  results['lock_released_when_loader_exits']='passed'

  p=setup(root,'server-mode');(p/'sbin/piforce/servermode.txt').write_text('serveron')
  a=start(new,p);wait_for(lambda:len(events(p))==1);b=start(new,p);wait_for(lambda:len(events(p))==2)
  (p/'release').touch();finish(a);finish(b)
  assert not (p/'run/wipi').exists()
  results['server_mode_management_remains_unchanged']='passed'

  p=setup(root,'sender-failure');(p/'release').touch();failed=start(new,p,exit_code=7)
  stdout,stderr=failed.communicate(timeout=4)
  assert failed.returncode==1,(stdout,stderr)
  state=json.loads(next((p/'run/wipi').glob('*.json')).read_text())
  assert state['state']=='error' and '7' in state['detail']
  later=start(new,p);finish(later)
  state=json.loads(next((p/'run/wipi').glob('*.json')).read_text())
  assert state['state']=='complete'
  results['sender_failure_recorded_and_next_launch_succeeds']='passed'


 print(json.dumps(results,indent=2))
finally:
 for p in processes:
  if p.poll()is None:p.kill();p.communicate()
