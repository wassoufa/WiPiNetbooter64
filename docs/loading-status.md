# Loading status enhancement

[PR #1](https://github.com/wassoufa/WiPiNetbooter64/pull/1) is merged source; deployment and cabinet acceptance of the new status enhancement remain pending. See [current state](ai-handoff.md), [the separate acceptance track](roadmap.md) and [the runtime evidence plan](native-runtime-test-plan.md) with its [result template](templates/runtime-test-result.md). This document owns behavior and deployment details, not the moving source/artifact snapshot.

The existing game list still selects a compatible configured NetDIMM. `load.php` validates the selected ROM against the game list and installed ROM directory, quotes each argument, starts the ordinary loader and immediately redirects to `loadprogress.php`. `loadnochrome.php` remains a compatibility entry point to the same flow. Chrome and mobile browsers no longer need separate streaming/wait loops.

Only a launch endpoint starts a loader. Progress polling, page refresh and the **Check status again** button never resend a game. If an active job is already known, a new launch follows its status. The backend lock remains the authority for simultaneous requests that race before status is written.

## Status ownership

`wipiloader.py` holds the ordinary-upload lock while setting up and waiting for `netdimm_send`. The `upload_status.py` helper atomically writes a root-owned, world-readable JSON record under `/run/wipi/upload-<target hash>.json`. The web process only reads it. The record includes a job ID, owner PID/start time, ROM, timestamps, progress-file baseline and terminal outcome. Runtime records disappear on reboot.

The web status reader combines that record with the existing `/var/log/progress_<IP>` file. Old COMPLETE contents are ignored until the progress file changes. Process start time prevents a reused PID from appearing to be the original loader.

- **Preparing**: the loader is setting up/decompressing/connecting, or has not written new transfer progress.
- **Uploading**: fresh progress is available. A live loader at 0% or with temporarily unchanged progress remains active, with a waiting explanation after 15 seconds; it is not automatically retried or declared failed.
- **Starting**: the upload progress says COMPLETE but the sender has not reported a successful exit yet.
- **Complete**: the sender exited successfully after its game-start command. This does not prove that the arcade board reached playable gameplay.
- **Error**: the sender failed, the owner exited unexpectedly, or a requested loader never started. No automatic game retry occurs. Relevant sender details are displayed when available.

Network failures while reading status have bounded retries, followed by a read-only retry button. They do not imply that the underlying upload stopped.

## Scope and compatibility

Single Boot, OSM payload generation, CRC bypass, NOW LOADING/reset behavior, networking and optional control/card setup are preserved. Persistent Server Mode keeps its existing manager lifecycle; its default game is managed from NetDIMM settings rather than this ordinary upload page. The guard still does not coordinate a simultaneous independent OSM/standalone utility transfer: finish the arcade-menu upload before starting a phone upload.

The phone launch URL remains compatible with existing links. It is still a legacy GET action; this change is not a complete authentication/CSRF redesign. The separate mobile launcher and game-library redesign are later features.

## Offline proof

From the repository root, with Docker available:

```sh
docker run --rm --network none -v "$PWD:/app" -w /app python:3.12-slim python -B tests/test_upload_lock.py
docker run --rm --network none -v "$PWD:/app:ro" -w /app python:3.12-slim python -B tests/test_upload_status.py
docker run --rm --network none -v "$PWD:/app:ro" -w /app php:8.4-cli-alpine php tests/test_upload_web.php
docker run --rm --network none -v "$PWD:/app:ro" -w /app php:8.4-cli-alpine php tests/test_osm_default.php
```

The loader tests replace outbound commands and hardware imports. The HTTP tests use the real PHP pages, a disposable loopback server and a fake worker; fixed `/run`, `/boot` and `/sbin` paths exist only inside the container. No game or NetDIMM connection is needed.

## Deployment and acceptance — not yet performed

Back up `wipiloader.py`, the four existing loading PHP pages, `loadcheck.php`, their owners/modes and any pre-existing new helper files. Deploy the Python helper before its caller and the PHP helper before its callers, with no active transfer or concurrent configuration editing. Preserve the current owners/modes; the Python helper is root-owned and readable by the loader. No reboot or service restart should be needed. Confirm the source hashes and rollback archive before any phone launch.

On hardware: verify a normal upload, duplicate request while active, a subsequent different game, OSM-to-phone switching after the OSM transfer finishes, and normal Single Boot startup. Confirm that an early 0% wait produces an explanation rather than another send. Error/interruption behavior must first be tested with fixtures; do not deliberately interrupt a live cabinet transfer just to test the error display.

Rollback all deployed files together with no active upload. Restoring the previous loading pages and loader returns to the already tested upload guard; remove only the newly added helpers if they did not exist before deployment. Keep cabinet CSV/settings and ROMs unchanged.
