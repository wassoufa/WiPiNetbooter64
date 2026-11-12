import importlib.util,json,os,stat,tempfile,unittest
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
    def test_failed_write_releases_lock(self):
        with patch.object(status.UploadStatus,'save',side_effect=OSError('fixture failure')):
            with self.assertRaises(OSError):status.UploadStatus('192.0.2.3','game.bin.gz')
        job=status.UploadStatus('192.0.2.3','game.bin.gz');job.close()

if __name__=='__main__':unittest.main()
