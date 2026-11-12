# Working on this fork

These instructions apply throughout the repository. Read the [README](README.md), [baseline](docs/fork-baseline.md) and [loading-status notes](docs/loading-status.md) before changing the loading or configuration paths. Keep these documents accurate when behavior or deployment status changes.

## Project and current state

- This is `wassoufa/WiPiNetbooter64`, based on `cassianoperin/WiPiNetbooter64`, ultimately derived from chunksin's WiPiNetbooter. Push fork work to `origin`; do not publish to `upstream` without an explicit request.
- The inspected installation runs `wipi 0.22-0` on Debian 13 arm64. The public upstream is an older source snapshot, not an exact representation of the installed package. Compare relevant installed files before preparing any deployment; never replace the entire installation from this checkout.
- The development cabinet uses Naomi 1 with physical JVS controls. Preserve support for the other systems and optional control/card integrations already present in the project.
- The OSM-save correction and ordinary-upload guard have passed cabinet tests. The first loading-status enhancement is implemented in [PR #1](https://github.com/wassoufa/WiPiNetbooter64/pull/1), with offline checks passing; it has not been deployed or accepted on hardware. Source merge and hardware acceptance are separate. Recheck current Git/PR state and deployment records before relying on this snapshot.
- Follow the README roadmap: finish loading-status acceptance before adding the proposed phone launcher, search/filter improvements, bulk list management or artwork changes. Candidates from other forks are references for selective adaptation, not approved wholesale replacements.

## Live-system boundaries

- Repository work does not authorize Pi changes. Prepare the concrete diff, backup/rollback procedure and test plan, then obtain approval for additional live changes unless the current session already explicitly authorizes them.
- Do not upgrade the OS or WiPi, alter networking/SSH, reboot/shut down, delete games or change cabinet power without explicit authorization. Coordinate any startup test with the user.
- Before an approved deployment, confirm no transfer or configuration edit is active. Back up affected files and their owners/modes, verify the archive and installed source hashes, and deploy only the reviewed files. Install new helpers before their callers and roll back the related files together. See the deployment section in `docs/loading-status.md`.
- Keep credentials, private addresses, cabinet CSV/settings, captured logs and ROMs out of commits. Existing repository defaults are not proof of current cabinet settings. Obtain access details through the authorized session rather than storing them here.
- Never use a live transfer to test forced failure or interruption. Use isolated fixtures. Do not trigger a game launch merely to inspect a page.

## Code map and ownership

| Path | Responsibility |
| --- | --- |
| `var/www/html/loadcheck.php` | Select compatible online NetDIMMs from the game-list flow. |
| `var/www/html/load.php` | Validate a launch and start the ordinary loader, or follow an active job; redirect immediately to status. |
| `var/www/html/loadnochrome.php` | Compatibility entry point to the same launch flow. |
| `var/www/html/upload_web.php` | Shared game/target validation and read-only job/progress interpretation. |
| `var/www/html/loadprogress.php` | Read-only HTML/JSON status and browser polling. |
| `sbin/piforce/wipiloader.py` | Ordinary upload transaction, optional control/card setup, sender invocation and Server Mode dispatch. |
| `sbin/piforce/upload_status.py` | Per-target lock and atomic loader-owned job records. |
| `sbin/piforce/dm_netboot/scripts/netdimm_send.py` | Sender command implementation; the adjacent top-level `netdimm_send` is its entry point. |
| `sbin/piforce/dm_netboot/netdimm/netdimm.py` | NetDIMM protocol and legacy per-target transfer progress. |
| `sbin/piforce/singleboot.py`, `sbin/piforce/menulauncher.py` | Startup/default selection and on-screen menu (OSM) integration. |
| `var/www/html/updatedimms.php` | NetDIMM CSV persistence, including the repaired OSM default serialization. |
| `native/netbootmenu/` | Experimental text-menu source; not selected by the installed launcher. Protocol layout in `protocol.h`, SRAM exchange in `sram.c`, rendering/control flow in `screens.c`. |

## Behavior to preserve

- Single Boot is critical to the cabinet's startup behavior. Preserve it, OSM payload generation and the default-game path.
- `dimms.csv` has eight fields: `name,ipaddress,type,opentarget,defaultgame,openjvs,openffb,cab`. Saving the menu default must expand it to `menu,none,none`; do not collapse the mapping columns or lose cabinet orientation. Preserve custom game entries, including the CRT tester.
- Acquire the nonblocking ordinary-upload lock **before** truncating logs or performing setup side effects. The lock is per target, not global. Rejected duplicates must leave the active job/progress intact; later explicit launches must work after completion or failure.
- Persistent Server Mode deliberately bypasses the ordinary lock and retains its manager/replacement lifecycle. The ordinary web launch page directs Server Mode users to NetDIMM settings.
- The lock does not coordinate independent OSM/standalone transfers. Finish the arcade-menu transfer before a phone launch; do not describe this as a system-wide upload scheduler.
- Only launch actions start a loader. Polling, refreshing and retrying a status read must never send or automatically retry a game.
- The loader owns atomic, root-owned, readable job JSON under `/run/wipi/upload-<target hash>.json`; PHP only reads it. Check PID start ticks as well as PID, and reject progress inherited from a previous launch. Legacy progress lives at `/var/log/progress_<IP>`.
- A live sender waiting at 0% is not evidence of failure. `COMPLETE` in the progress file is not sufficient for success: wait for successful sender exit. Even that does not prove playable gameplay; get cabinet confirmation.
- Preserve the existing five-second OpenFFB delay, CRC bypass, NOW LOADING/reset behavior and optional control/card setup unless a separately scoped change explicitly calls for altering them.
- Validate configured targets, known enabled/installed ROMs and system compatibility at the launch boundary. Resolve mappings from trusted metadata and quote each shell argument individually. The existing GET launch action is not a complete authentication/CSRF design; do not claim otherwise.
- For future CSV edits, use locked, same-directory atomic updates that preserve ownership/modes and all unrelated rows/columns. Browser-only hiding is distinct from OSM enable/disable behavior.

## Focused verification

Run the relevant checks from the repository root. These tests use fake hardware/senders. **Run the PHP tests in disposable containers:** they create fixtures at fixed `/run`, `/boot`, `/sbin` and `/tmp` paths and must not run directly on the Pi or host. Images must already be available for offline execution.

```sh
docker run --rm --network none -v "$PWD:/app" -w /app python:3.12-slim python -B tests/test_upload_lock.py
docker run --rm --network none -v "$PWD:/app:ro" -w /app python:3.12-slim python -B tests/test_upload_status.py
docker run --rm --network none -v "$PWD:/app:ro" -w /app php:8.4-cli-alpine php tests/test_upload_web.php
docker run --rm --network none -v "$PWD:/app:ro" -w /app php:8.4-cli-alpine php tests/test_osm_default.php
git diff --check
```

For changed PHP files, also run `php -l` inside the PHP container. Loading changes need coverage of duplicate suppression, per-target independence, later launches, sender failure, stale completion, live 0% waits and read-only polling. Configuration serialization changes need the eight-field OSM regression check. Documentation-only changes need link/path and diff checks, not another hardware test.

After approved deployment, use the acceptance checklist in `docs/loading-status.md`. Report offline results separately from hardware observations and state what remains unverified. Update the README and deployment notes when acceptance or rollback occurs.

## Deferred investigations

The [illustrated OSM investigation](docs/illustrated-osm-investigation.md) is a separate roadmap candidate: native artwork plus joystick selection, not a web-page change. The [native baseline](native/README.md) vendors renderer source from hmofet/netboot `6ccbfdd000e705678ee422ebe972c2fccce40693`, adds WiPi's SRAM configuration/exchange and compiles locally. Run `python3 -B tests/test_native_menu.py` for changes to its wire/SRAM code and `sh native/build.sh` for native changes. Keep the shipped runtime binaries intact; local build success is not emulator/cabinet acceptance. Artifacts under `native/out/` and build caches are ignored. No native artwork has been implemented yet. Preserve source/asset provenance and font notices.

See [CRT follow-up](docs/crt-sync-follow-up.md). The Toshiba PD2367 is already at 31 kHz; clicks accompany signal loss/return during Naomi reset. Sync reacquisition is a working explanation, not a diagnosis of chassis damage. `--disable-now-loading` is a candidate for a controlled comparison; the final reboot remains. Do not change reset timing as part of unrelated features, bypass protection/relays or modify the chassis to suppress clicking.
