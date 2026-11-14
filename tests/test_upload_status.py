import importlib.util,json,os,stat,tempfile,unittest
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch

path=Path(__file__).resolve().parents[1]/'sbin/piforce/upload_status.py'
spec=importlib.util.spec_from_file_location('upload_status',path)
status=importlib.util.module_from_spec(spec);spec.loader.exec_module(status)

class UploadStateTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.patch=patch.object(status,'RUNTIME_DIR',self.temp.name);self.patch.start()
    def tearDown(self):
        self.patch.stop();self.temp.cleanup()
    def test_busy_does_not_replace_the_active_job(self):
        job=status.UploadStatus('192.0.2.3','game.bin.gz')
        try:
            before=Path(job.path).read_bytes()
            with self.assertRaises(status.UploadBusy):status.UploadStatus('192.0.2.3','other.bin.gz')
            self.assertEqual(Path(job.path).read_bytes(),before)
            self.assertEqual(stat.S_IMODE(Path(job.path).stat().st_mode),0o644)
            self.assertEqual(job.state['process_start'],status.process_start(os.getpid()))
            job.finish(True)
            self.assertEqual(json.loads(Path(job.path).read_text())['state'],'complete')
        finally:job.close()
        later=status.UploadStatus('192.0.2.3','later.bin.gz');later.close()
    def test_exceptional_exit_records_interruption(self):
        job=status.UploadStatus('192.0.2.3','game.bin.gz');job.close()
        self.assertEqual(json.loads(Path(job.path).read_text())['state'],'error')
    def test_different_targets_are_independent(self):
        one=status.UploadStatus('192.0.2.3','one.bin.gz');two=status.UploadStatus('192.0.2.4','two.bin.gz')
        self.assertNotEqual(one.path,two.path);one.close();two.close()
    def test_failed_initialization_closes_file_and_allows_later_launch(self):
        # Retain every real handle: collection must not be what releases the lock.
        opened=[]
        def track_open(*args,**kwargs):
            handle=open(*args,**kwargs)
            if str(args[0]).endswith('.lock'):opened.append(handle)
            return handle
        failures=[
            (status.fcntl,'flock',OSError('flock failure')),
            (status,'file_hash',OSError('progress read failure')),
            (status.os,'stat',PermissionError('progress stat failure')),
            (status.uuid,'uuid4',RuntimeError('job id failure')),
            (status,'process_start',OSError('process identity failure')),
            (status.time,'time',KeyboardInterrupt()),
            (status.UploadStatus,'save',OSError('status write failure')),
        ]
        for owner,name,error in failures:
            with self.subTest(stage=name):
                side_effect=error
                if owner is status.os:
                    real_stat=os.stat
                    def fail_progress_stat(path,*args,**kwargs):
                        if str(path).startswith('/var/log/progress_'):raise error
                        return real_stat(path,*args,**kwargs)
                    side_effect=fail_progress_stat
                with ExitStack() as stack:
                    stack.enter_context(patch.object(status,'open',side_effect=track_open,create=True))
                    stack.enter_context(patch.object(owner,name,side_effect=side_effect))
                    with self.assertRaises(type(error)) as caught:
                        status.UploadStatus('192.0.2.3','game.bin.gz')
                    self.assertIs(caught.exception,error)
                    self.assertTrue(opened[-1].closed)
                job=status.UploadStatus('192.0.2.3','later.bin.gz');job.close()
        self.assertEqual(len(opened),len(failures))
    def test_busy_initialization_closes_only_the_rejected_file(self):
        active=status.UploadStatus('192.0.2.3','game.bin.gz')
        opened=[]
        def track_open(*args,**kwargs):
            handle=open(*args,**kwargs);opened.append(handle);return handle
        try:
            before=Path(active.path).read_bytes()
            with patch.object(status,'open',side_effect=track_open,create=True):
                with self.assertRaises(status.UploadBusy):
                    status.UploadStatus('192.0.2.3','other.bin.gz')
            self.assertEqual(len(opened),1)
            self.assertTrue(opened[0].closed)
            self.assertFalse(active.lock.closed)
            self.assertEqual(Path(active.path).read_bytes(),before)
        finally:active.close()

if __name__=='__main__':unittest.main()
