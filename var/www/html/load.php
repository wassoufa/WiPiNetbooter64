<?php
require_once __DIR__ . '/upload_web.php';

try {
    $target = upload_target($_GET['dimm'] ?? '');
    $game = upload_game($_GET['rom'] ?? '');
    if (!$game['enabled'] || !is_file('/boot/roms/' . $game['rom'])) {
        throw new InvalidArgumentException('The selected game is disabled or its ROM file is missing.');
    }
    if (!in_array($game['system'], upload_supported_systems($target['type']), true)) {
        throw new InvalidArgumentException('The selected game is not compatible with this NetDIMM.');
    }
    if (trim(file_get_contents('/sbin/piforce/servermode.txt')) === 'serveron') {
        throw new InvalidArgumentException('Server Mode is active. Change its default game in Manage NetDIMMs.');
    }
    $existing = upload_status($target['ip']);
    $busy = in_array($existing['state'], ['preparing', 'uploading', 'starting'], true);
    $since = $busy ? 0 : microtime(true);
    if (!$busy) {
        $args = [$game['rom'], $target['ip'],
            trim(file_get_contents('/sbin/piforce/relaymode.txt')),
            trim(file_get_contents('/sbin/piforce/zeromode.txt')), $game['mapping'], $game['ffb']];
        $command = 'sudo python3 /sbin/piforce/wipiloader.py ' . implode(' ', array_map('escapeshellarg', $args));
        exec($command . ' > /dev/null 2>&1 &');
    }
    header('Cache-Control: no-store');
    header('Location: loadprogress.php?' . http_build_query([
        'dimm' => $target['ip'], 'since' => sprintf('%.6F', $since), 'follow' => $busy ? '1' : '0'
    ], '', '&', PHP_QUERY_RFC3986), true, 303);
    exit;
} catch (InvalidArgumentException $error) {
    upload_error_page($error->getMessage());
} catch (Exception $error) {
    error_log('WiPi launch request failed: ' . $error->getMessage());
    upload_error_page('WiPi could not start the loader. Check the web error log.', 500);
}
