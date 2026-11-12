<?php
require_once __DIR__ . '/upload_web.php';
header('Cache-Control: no-store');
try {
    $target = upload_target($_GET['dimm'] ?? '');
    $since = $_GET['since'] ?? '0';
    if (!is_string($since) || !is_numeric($since) || (float)$since < 0 || (float)$since > microtime(true) + 1) {
        throw new InvalidArgumentException('The upload status request is invalid.');
    }
    $since = (float)$since;
    $status = upload_status($target['ip'], $since);
    if (($_GET['format'] ?? '') === 'json') {
        header('Content-Type: application/json; charset=utf-8');
        echo json_encode($status, JSON_INVALID_UTF8_SUBSTITUTE);
        exit;
    }
} catch (Exception $error) {
    if (($_GET['format'] ?? '') === 'json') {
        http_response_code(400);
        header('Content-Type: application/json; charset=utf-8');
        echo json_encode(['state' => 'error', 'message' => $error->getMessage(), 'progress' => null]);
    } else {
        upload_error_page($error->getMessage());
    }
    exit;
}
$query = ['dimm' => $target['ip'], 'since' => sprintf('%.6F', $since)];
$statusUrl = 'loadprogress.php?' . http_build_query($query + ['format' => 'json'], '', '&', PHP_QUERY_RFC3986);
$refreshUrl = 'loadprogress.php?' . http_build_query($query, '', '&', PHP_QUERY_RFC3986);
?>
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>WiPi — game upload</title>
<style>
body{font:1.1rem/1.5 system-ui,sans-serif;background:#151515;color:#eee;margin:0;padding:1.5rem}main{max-width:36rem;margin:3rem auto}a{color:#8ad5ff}progress{width:100%;height:2rem}h1{overflow-wrap:anywhere}#message{min-height:3rem}pre{white-space:pre-wrap;overflow-wrap:anywhere;font-size:.85rem}#busy{border-left:4px solid #8ad5ff;padding-left:1rem}button{font:inherit;padding:.6rem 1rem;margin:.5rem 0}
</style>
</head>
<body><main>
<p><a href="gamelist.php?display=all">Back to games</a></p>
<h1 id="game"><?= upload_escape($status['name'] ?? 'Game upload') ?></h1>
<p>NetDIMM: <?= upload_escape($target['name']) ?></p>
<p id="busy" <?= ($_GET['follow'] ?? '') === '1' ? '' : 'hidden' ?>>An upload is already in progress. Following that upload.</p>
<p id="message" role="status" aria-live="polite"><?= upload_escape($status['message']) ?></p>
<progress id="progress" max="100" aria-label="Game upload progress" <?= is_int($status['progress']) ? 'value="' . $status['progress'] . '"' : '' ?>></progress>
<p id="percent"><?= is_int($status['progress']) ? $status['progress'] . '%' : '' ?></p>
<details id="details" <?= empty($status['detail']) ? 'hidden' : '' ?>><summary>Error details</summary><pre id="detail"><?= upload_escape($status['detail'] ?? '') ?></pre></details>
<p id="connection" role="status" aria-live="polite"></p>
<button id="refresh" type="button" hidden>Check status again</button>
<noscript><p><a href="<?= upload_escape($refreshUrl) ?>">Refresh upload status</a>. Refreshing this page does not resend the game.</p></noscript>
</main>
<script>
(function () {
    'use strict';
    const url = <?= json_encode($statusUrl, JSON_HEX_TAG | JSON_HEX_AMP | JSON_HEX_APOS | JSON_HEX_QUOT) ?>;
    let failures = 0;
    let active = true;
    function render(data) {
        if (data.name) document.getElementById('game').textContent = data.name;
        document.getElementById('message').textContent = data.message;
        const bar = document.getElementById('progress');
        if (Number.isInteger(data.progress)) {
            bar.value = data.progress;
            document.getElementById('percent').textContent = data.progress + '%';
        } else {
            bar.removeAttribute('value');
            document.getElementById('percent').textContent = '';
        }
        const failed = data.state === 'error';
        document.getElementById('details').hidden = !failed || !data.detail;
        document.getElementById('detail').textContent = data.detail || '';
        active = !['complete', 'error', 'idle'].includes(data.state);
        if (!active) document.getElementById('busy').hidden = true;
        bar.setAttribute('aria-busy', active ? 'true' : 'false');
    }
    async function poll() {
        try {
            const response = await fetch(url, {cache: 'no-store'});
            if (!response.ok) throw new Error('Status request failed');
            render(await response.json());
            failures = 0;
            document.getElementById('connection').textContent = '';
            document.getElementById('refresh').hidden = true;
            if (active) setTimeout(poll, 1000);
        } catch (error) {
            failures++;
            document.getElementById('connection').textContent = 'Cannot read upload status. This does not start another transfer.';
            if (failures < 3) setTimeout(poll, 2000);
            else document.getElementById('refresh').hidden = false;
        }
    }
    document.getElementById('refresh').addEventListener('click', function () {
        failures = 0; this.hidden = true; poll();
    });
    render(<?= json_encode($status, JSON_HEX_TAG | JSON_HEX_AMP | JSON_HEX_APOS | JSON_HEX_QUOT | JSON_INVALID_UTF8_SUBSTITUTE) ?>);
    if (active) setTimeout(poll, 500);
}());
</script></body></html>
