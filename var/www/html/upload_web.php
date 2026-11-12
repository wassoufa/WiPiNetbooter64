<?php
// Read-only status helpers. Only load.php starts a loader; polling never does.
const WIPI_RUNTIME_DIR = '/run/wipi';

function upload_target($value) {
    if (!is_string($value) || !filter_var($value, FILTER_VALIDATE_IP, FILTER_FLAG_IPV4)) {
        throw new InvalidArgumentException('Choose a configured NetDIMM.');
    }
    $file = fopen(__DIR__ . '/csv/dimms.csv', 'r');
    if (!$file) {
        throw new RuntimeException('The NetDIMM configuration could not be read.');
    }
    fgetcsv($file, 0, ',', '"', '');
    while (($row = fgetcsv($file, 0, ',', '"', '')) !== false) {
        if (count($row) >= 3 && $row[1] === $value) {
            fclose($file);
            return ['ip' => $value, 'name' => $row[0], 'type' => $row[2]];
        }
    }
    fclose($file);
    throw new InvalidArgumentException('That NetDIMM is not configured.');
}

function upload_supported_systems($type) {
    $systems = [
        'Sega Naomi' => ['Sega Naomi', 'Sammy Atomiswave'],
        'Sega Naomi2' => ['Sega Naomi', 'Sega Naomi2', 'Sammy Atomiswave'],
        'Sega Chihiro' => ['Sega Chihiro'],
        'Sega Triforce' => ['Sega Triforce'],
    ];
    return $systems[$type] ?? [];
}

function upload_game($rom) {
    if (!is_string($rom) || $rom === '' || basename($rom) !== $rom || strpos($rom, '\\') !== false || strpos($rom, "\0") !== false) {
        throw new InvalidArgumentException('Choose a game from the game list.');
    }
    $file = fopen(__DIR__ . '/csv/romsinfo.csv', 'r');
    if (!$file) {
        throw new RuntimeException('The game list could not be read.');
    }
    fgetcsv($file, 0, ',', '"', '');
    while (($row = fgetcsv($file, 0, ',', '"', '')) !== false) {
        if (count($row) >= 16 && $row[1] === $rom) {
            fclose($file);
            return ['rom' => $rom, 'name' => $row[4], 'system' => $row[0],
                'enabled' => $row[12] === 'Yes', 'mapping' => $row[14], 'ffb' => $row[15]];
        }
    }
    fclose($file);
    throw new InvalidArgumentException('That game is not in the game list.');
}

function upload_read_job($target) {
    $path = WIPI_RUNTIME_DIR . '/upload-' . hash('sha256', $target) . '.json';
    $raw = @file_get_contents($path);
    $job = $raw === false ? null : json_decode($raw, true);
    if (!is_array($job) || ($job['version'] ?? null) !== 1 || ($job['target'] ?? '') !== $target
        || !isset($job['id'], $job['rom'], $job['pid'], $job['process_start'], $job['started'], $job['state'])) {
        return null;
    }
    return $job;
}

function upload_process_alive($job) {
    if (!is_int($job['pid']) || $job['pid'] <= 0) {
        return false;
    }
    $raw = @file_get_contents('/proc/' . $job['pid'] . '/stat');
    if ($raw === false || ($end = strrpos($raw, ')')) === false) {
        return false;
    }
    $fields = preg_split('/\s+/', trim(substr($raw, $end + 1)));
    return isset($fields[19]) && !in_array($fields[0], ['Z', 'X'], true)
        && $fields[19] === (string)$job['process_start'];
}

function upload_pending($since) {
    if ($since > 0 && microtime(true) - $since >= 10) {
        return ['state' => 'error', 'message' => 'The loader did not start. No automatic retry was made.', 'progress' => null];
    }
    return ['state' => 'preparing', 'message' => 'Waiting for the loader to start…', 'progress' => null];
}

function upload_status($target, $since = 0) {
    $job = upload_read_job($target);
    if ($job === null) {
        return $since > 0 ? upload_pending($since) : ['state' => 'idle', 'message' => 'No upload is recorded for this NetDIMM.', 'progress' => null];
    }
    if ($job['state'] === 'active' && !upload_process_alive($job)) {
        // The loader may have finished between reading the JSON and checking its PID.
        $job = upload_read_job($target) ?? $job;
    }
    $alive = $job['state'] === 'active' && upload_process_alive($job);
    if (!$alive && (float)$job['started'] < $since) {
        return upload_pending($since);
    }
    $name = $job['rom'];
    try { $name = upload_game($job['rom'])['name']; } catch (Exception $ignored) {}
    $common = ['id' => $job['id'], 'name' => $name, 'target' => $target, 'started' => $job['started']];
    if ($job['state'] === 'complete') {
        return $common + ['state' => 'complete', 'message' => 'Transfer complete. The arcade board has been told to start the game.', 'progress' => 100];
    }
    if ($job['state'] === 'error' || !$alive) {
        return $common + ['state' => 'error', 'message' => 'The upload stopped before it completed. No automatic retry was made.',
            'detail' => $job['detail'] ?? 'The loader exited unexpectedly.', 'progress' => null];
    }
    $path = '/var/log/progress_' . $target;
    $raw = @file_get_contents($path);
    // Content identity prevents an old COMPLETE from being mistaken for this launch,
    // even when two launches have timestamps in the same filesystem second.
    clearstatcache(true, $path);
    $mtime = @filemtime($path);
    $unchanged = $raw !== false && hash('sha256', $raw) === ($job['progress_baseline'] ?? null)
        && ($mtime === false || $mtime <= ($job['progress_baseline_mtime'] ?? PHP_INT_MAX));
    if ($raw === false || $unchanged) {
        return $common + ['state' => 'preparing', 'message' => 'Preparing the game and connecting to the NetDIMM…', 'progress' => null];
    }
    $lines = preg_split('/\r?\n/', trim($raw));
    $last = end($lines);
    if ($last === 'COMPLETE') {
        return $common + ['state' => 'starting', 'message' => 'Upload sent. Waiting for the game-start command to finish…', 'progress' => 100];
    }
    if (!ctype_digit($last) || (int)$last > 100) {
        return $common + ['state' => 'preparing', 'message' => 'Waiting for transfer progress…', 'progress' => null];
    }
    $progress = (int)$last;
    clearstatcache(true, $path);
    $waiting = time() - (int)@filemtime($path) >= 15;
    $message = $waiting ? 'The loader is still running. Waiting for transfer progress…'
        : ($progress === 0 ? 'Starting the transfer. Progress may stay at 0% briefly.' : 'Uploading the game…');
    return $common + ['state' => 'uploading', 'message' => $message, 'progress' => $progress];
}

function upload_escape($value) {
    return htmlspecialchars((string)$value, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8');
}

function upload_error_page($message, $status = 400) {
    http_response_code($status);
    header('Cache-Control: no-store');
    echo '<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">';
    echo '<title>WiPi — unable to load</title><main><h1>Unable to start the upload</h1><p>' . upload_escape($message) . '</p>';
    echo '<p><a href="gamelist.php?display=all">Back to games</a></p></main></html>';
}
