<?php
// Isolated HTTP-test worker. Never imports or invokes the real loader.
$rom = $argv[3]; $target = $argv[4];
file_put_contents('/tmp/wipi-web-launches', json_encode($argv) . "\n", FILE_APPEND | LOCK_EX);
$path = '/run/wipi/upload-' . hash('sha256', $target) . '.json';
$stat = file_get_contents('/proc/' . getmypid() . '/stat');
$fields = preg_split('/\s+/', trim(substr($stat, strrpos($stat, ')') + 1)));
$progress = '/var/log/progress_' . $target;
$job = ['version' => 1, 'id' => bin2hex(random_bytes(16)), 'target' => $target, 'rom' => $rom,
    'pid' => getmypid(), 'process_start' => $fields[19], 'started' => microtime(true),
    'state' => 'active', 'progress_baseline' => hash_file('sha256', $progress),
    'progress_baseline_mtime' => filemtime($progress)];
function save_fake($path, $job) {
    $tmp = $path . '.tmp'; file_put_contents($tmp, json_encode($job)); rename($tmp, $path);
}
save_fake($path, $job);
$deadline = microtime(true) + 15;
while (!file_exists('/tmp/wipi-web-release') && microtime(true) < $deadline) usleep(20000);
$job['state'] = 'complete'; save_fake($path, $job);
