<?php
// Run in a disposable PHP container: fixed /run, /boot and /sbin paths stay isolated.
function check($condition, $message) { if (!$condition) throw new Exception($message); }
$root = dirname(__DIR__);
$web = sys_get_temp_dir() . '/wipi-web-' . getmypid();
mkdir($web . '/csv', 0777, true);
foreach (['upload_web.php','load.php','loadnochrome.php','loadprogress.php'] as $file) copy($root . '/var/www/html/' . $file, $web . '/' . $file);
require $web . '/upload_web.php';
$target = '192.0.2.3'; $rom = 'test game[1].bin.gz';
file_put_contents($web . '/csv/dimms.csv', "name,ipaddress,type,opentarget,defaultgame,openjvs,openffb,cab\nTest,192.0.2.3,Sega Naomi,off,menu,none,none,horizontal\n");
$file = fopen($web . '/csv/romsinfo.csv', 'w');
fputcsv($file, array_fill(0, 18, 'header'), ',', '"', '');
$row = array_fill(0, 18, '');
$row[0]='Sega Naomi'; $row[1]=$rom; $row[4]='Test <script>alert(1)</script> & "game"'; $row[12]='Yes'; $row[14]='generic'; $row[15]='none';
fputcsv($file, $row, ',', '"', '');
$row[1]='disabled.bin.gz'; $row[12]='No'; fputcsv($file, $row, ',', '"', ''); fclose($file);
mkdir('/run/wipi', 0755, true); mkdir('/boot/roms', 0755, true); mkdir('/sbin/piforce', 0755, true);
file_put_contents('/boot/roms/' . $rom, 'fixture'); file_put_contents('/boot/roms/disabled.bin.gz', 'fixture');
foreach (['servermode'=>'serveroff','relaymode'=>'relayoff','zeromode'=>'hackoff'] as $key=>$value) file_put_contents('/sbin/piforce/' . $key . '.txt', $value);
$path = '/run/wipi/upload-' . hash('sha256', $target) . '.json';
$progress = '/var/log/progress_' . $target;
$raw = file_get_contents('/proc/' . getmypid() . '/stat');
$fields = preg_split('/\s+/', trim(substr($raw, strrpos($raw, ')') + 1)));
file_put_contents($progress, "0\n99\nCOMPLETE");
$job = ['version'=>1,'id'=>'fixture','target'=>$target,'rom'=>$rom,'pid'=>getmypid(),
    'process_start'=>$fields[19],'started'=>microtime(true),'state'=>'active',
    'progress_baseline'=>hash_file('sha256',$progress),'progress_baseline_mtime'=>filemtime($progress)];
function save_job($job) { global $path; file_put_contents($path, json_encode($job)); }
check(upload_status($target, microtime(true))['state']==='preparing','Missing job must wait');
check(upload_status($target, microtime(true)-11)['state']==='error','Missing loader must report failure');
save_job($job);
check(upload_status($target)['state']==='preparing','Old COMPLETE must not complete the new job');
$fresh=$job; $fresh['progress_baseline_mtime']-=10; save_job($fresh);
check(upload_status($target)['state']==='starting','New completion with matching contents must be recognized by its changed timestamp');
save_job($job);
file_put_contents($progress,"0\n"); touch($progress,time()-40);
$status=upload_status($target);
check($status['state']==='uploading' && $status['progress']===0,'A live 0% upload must remain active');
check(str_contains($status['message'],'still running'),'A long 0% wait must be explained');
file_put_contents($progress,"0\n100\nCOMPLETE");
check(upload_status($target)['state']==='starting','COMPLETE alone must wait for successful sender exit');
$wrong=$job; $wrong['process_start']='0'; save_job($wrong);
check(upload_status($target)['state']==='error','PID reuse must not report a running upload');
$dead=$job; $dead['pid']=2147483647; save_job($dead);
check(upload_status($target)['state']==='error','Exited loader must not report success from progress alone');
$done=$job; $done['state']='complete'; save_job($done);
check(upload_status($target)['state']==='complete','Confirmed completion must be shown');
check(upload_status($target,microtime(true)+.01)['state']==='preparing','A new request must not inherit old success');
$failed=$job; $failed['state']='error'; $failed['detail']='fixture error'; save_job($failed);
check(upload_status($target)['detail']==='fixture error','Failure details must be preserved');
foreach (['../../etc/passwd','other.bin.gz'] as $bad) {
    $rejected=false; try { upload_game($bad); } catch (InvalidArgumentException $error) { $rejected=true; }
    check($rejected,'Unknown/traversal ROM accepted');
}
check(upload_supported_systems('Sega Naomi')===['Sega Naomi','Sammy Atomiswave'],'Naomi 1 compatibility changed');
unlink($path); file_put_contents($progress,"0\n99\nCOMPLETE");

// Exercise the actual PHP entry points over HTTP with a controlled fake sender.
$bin=$web.'/bin'; mkdir($bin);
file_put_contents($bin.'/sudo', "#!/bin/sh\nexec " . escapeshellarg(PHP_BINARY) . ' ' . escapeshellarg($root.'/tests/fixtures/fake_web_loader.php') . ' "$@"' . "\n"); chmod($bin.'/sudo',0755);
$port=random_int(19000,29000); $serverLog=$web.'/server.log';
$env=getenv(); $env['PATH']=$bin.':'.$env['PATH'];
$server=proc_open([PHP_BINARY,'-S','127.0.0.1:'.$port,'-t',$web],[0=>['pipe','r'],1=>['file',$serverLog,'a'],2=>['file',$serverLog,'a']],$pipes,null,$env);
function request_test($path) {
    global $port;
    $context=stream_context_create(['http'=>['ignore_errors'=>true,'follow_location'=>0,'timeout'=>2]]);
    $body=file_get_contents('http://127.0.0.1:'.$port.'/'.$path,false,$context);
    return [$http_response_header,$body];
}
function wait_test($test) {
    $deadline=microtime(true)+4;
    while (!$test()) { if (microtime(true)>$deadline) throw new Exception('Timed out waiting for fixture'); usleep(20000); }
}
try {
    wait_test(function() use($port) { $socket=@fsockopen('127.0.0.1',$port); if ($socket) fclose($socket); return (bool)$socket; });
    $query=http_build_query(['rom'=>$rom,'dimm'=>$target,'mapping'=>'untrusted','ffb'=>'untrusted']);
    [$headers,$body]=request_test('load.php?'.$query);
    check(str_contains($headers[0],'303'),'Launch must redirect immediately to a read-only status page');
    $location=''; foreach ($headers as $header) if (str_starts_with($header,'Location: ')) $location=substr($header,10);
    check(str_starts_with($location,'loadprogress.php?'),'Wrong launch redirect');
    wait_test(function() use($target) { $job=upload_read_job($target); return $job && upload_process_alive($job); });
    [$headers,$body]=request_test('load.php?'.$query);
    check(str_contains(implode('\n',$headers),'follow=1'),'A repeated launch must follow the busy upload');
    $statusPath='loadprogress.php?'.http_build_query(['dimm'=>$target,'format'=>'json']);
    for($i=0;$i<5;$i++) {
        [$headers,$body]=request_test($statusPath);
        check(json_decode($body,true)['state']==='preparing','Stale COMPLETE leaked through HTTP status');
    }
    [$headers,$html]=request_test($location);
    check(str_contains($html,'&lt;script&gt;'),'Game name must be HTML escaped');
    check(!str_contains($html,'<script>alert(1)</script>'),'Unescaped game metadata');
    $launches=file('/tmp/wipi-web-launches',FILE_IGNORE_NEW_LINES);
    check(count($launches)===1,'Polling or duplicate request started a second worker');
    $args=json_decode($launches[0],true);
    check($args[3]===$rom && $args[7]==='generic' && $args[8]==='none','Arguments split or request mapping was trusted');
    [$headers,$body]=request_test('load.php?'.http_build_query(['rom'=>'disabled.bin.gz','dimm'=>$target]));
    check(str_contains($headers[0],'400'),'Disabled game accepted');
    [$headers,$body]=request_test('loadprogress.php?dimm=../../etc/passwd&format=json');
    check(str_contains($headers[0],'400'),'Invalid status target accepted');
    touch('/tmp/wipi-web-release');
    wait_test(function() use($target) { return upload_status($target)['state']==='complete'; });
    [$headers,$body]=request_test($statusPath);
    check(json_decode($body,true)['state']==='complete','HTTP completion missing');
    [$headers,$body]=request_test('loadnochrome.php?'.$query);
    check(str_contains($headers[0],'303'),'Legacy mobile entry point must use the same flow');
    wait_test(function() { return count(file('/tmp/wipi-web-launches'))===2; });
    echo "PASS: status states, stale progress, 0% waits, failure/PID checks, validation, HTTP launch/busy/poll/completion, escaping and mobile compatibility\n";
} finally {
    touch('/tmp/wipi-web-release');
    proc_terminate($server); proc_close($server);
}
