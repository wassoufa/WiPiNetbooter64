# Naomi Phase B1: read-only preflight, 2026-11-13

The user approved the [Phase B1 settings-only plan](../native-naomi-settings-plan.md) in chat on 2026-11-13 (evening, Australia/Melbourne), including the startup EEPROM clear/write and incomplete physical rollback, and asked for preflight to start. This record covers preflight only. **Nothing was uploaded, staged, stopped or changed on the Pi or Naomi.** Naomi was OFF per the user. Execution still needs the user at the cabinet and an explicit go.

## What was checked (Pi time 2026-11-13T07:26:20Z, by Claude)

Access was the Pi's existing web file-manager shell, read-only commands only (`sudo -n python3` stat/hash, `ps`, and `tar` streamed to stdout). No file was written on the Pi.

| Check | Result |
| --- | --- |
| 30 installed regular files from the Phase A backup list: SHA-256, numeric UID/GID, mode | All match the Phase A preflight backup except `/var/log/netdimm_menu.log` (expected log change). Includes original menu variants, host/wrappers/transports, CSV/catalog, settings/mode files and `/var/log/menudump.bin`. |
| SRAM directory | `README.txt` only. |
| Host processes | No `netdimm_menu`, `menulauncher`, `wipiloader` or `singleboot` process running. Consistent with Naomi OFF; the original host is **not** currently waiting. |
| Fresh private backup | 30 files, 2,328,083 bytes. Every archive member's hash, mode and numeric owner was verified against the live state. |
| Installed `netdimm_menu.py` | Byte-identical to the repository copy at `sbin/piforce/dm_netboot/scripts/netdimm_menu.py`, so the plan's source references apply to the installed host. |
| Host options | `--exe`, `--menu-settings-file`, `--verbose` exist. `--persistent` and `--debug-mode` exist and must not be used. |
| Verbose evidence | Installed `netdimm/message.py` prints `Sending type: 0x…` and `Received type: 0x…` with lengths when verbose. This goes to **stdout**, not `/var/log/netdimm_menu.log`, so the candidate host's stdout must be captured to verify the forbidden-message checks. |
| Save ACK | Confirmed in installed source: `0x1008` is sent outside the index-match block. Not relevant to B1 (no save), relevant to any later B2. |
| Settings clone | Fresh private clone is byte-identical to the installed YAML and to the Phase A clone; `sram_save: false`. |
| Candidate | `native/out/netbootmenu.bin` is `45ef4f20…` (1,461,916 bytes), matching the plan. |

## Not done, and limits

- At Claude's preflight checkpoint, recovery rehearsal had not been repeated. The primary agent subsequently restored all **30 regular files** from this archive into a disposable container tmpfs with network disabled and the evidence mounted read-only. File bytes, SHA-256, numeric UID/GID and modes matched the manifest for every restored file. The private result is `restore-verification.json` beside the backup. No installed file or physical EEPROM/SRAM was restored.
- Catalog index/title/serial reconciliation happens at execution: IDs are regenerated per host launch.
- The test game has not been chosen. The user picks it at the cabinet.
- Because no host is running, B1 execution starts with Naomi power-on by the user; the first upload is then the candidate. The "original return" upload is the second and last.
- Hashes, addresses, paths and settings content stay private in outer `work/naomi-b1-preflight-20261113/` (`live-state.json`, `backup-manifest.json`, `installed-backup.tar.gz`, `candidate-settings-clone.yaml`, `preflight.py`).
- State can change before execution. Rerun `preflight.py` immediately before the run and compare with `backup-manifest.json`.
