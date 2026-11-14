# Prepared Naomi text-menu comparison (N0)

This document preserves the reviewed N0 preparation and case boundaries. The user subsequently approved and completed Phase A; see the [dated hardware result](results/2026-11-13-naomi-phase-a.md). Original and candidate directional cases/60-second idle were reported normal/stable. The original shipped menu was returned, and the user confirmed its menu and controls work. The candidate is not selected persistently; no additional action is authorized by this plan.

## Current outcome and readiness history

Sol prepared the package and Astra passed its readiness review. The user approved the two upload/reset cycles and startup EEPROM effects/incomplete physical rollback. The existing installed host temporarily selected the verified candidate with a regular SRAM-OFF clone, then returned the installed original with real settings. No Start, Test/Service, settings/save, games, SRAM enable, optional debug or AI power/startup actions occurred. Post-run checks matched all 24 installed non-log regular files on SHA-256/numeric ownership/modes and private live-session evidence was archived; runtime acceptance is limited to the dated observations.

Before the comparison, original controls recovered after the user's manual restart; the nonpersistent host exited. Original pre-BIOS/restored configured payloads were byte-identical, and no JVS root cause was proven. After recovery, the original baseline and candidate cases both passed user observations; a new original host remains active after the explicit return.

Preparation reverified 22 source hashes, base ROM and exact clone. A fresh 34-member private archive passed disposable offline recovery rehearsal of bytes/hashes/numeric ownership/modes, using existing `python:3.12-slim` image `sha256:dd29372629eeba2dd003fd9e9d35a5b8236c44727875a0364254b5127af88e65` with networking disabled, read-only container and temporary restore filesystem. This did not restore installed files or physical EEPROM/SRAM. Private read-only clock samples had maximum round-trip 0.045 seconds and no clocks changed; they do not prove synchronized clocks.

The next bounded action is review of the limited Phase A result and separately scoped remaining tests; post-run evidence/metadata verification is complete. Later settings/Start/game/SRAM phases remain separately gated and require fresh authorization. The remainder of this document records the approved preparation and future-case safety boundaries, not an instruction to repeat the run.

## Candidate and installed host compatibility

The inspected private installed-source backup uses the existing `netdimm_menu --exe` argument to open a raw base menu, append configuration at `0x0D000000`, write `/var/log/menudump.bin`, upload with CRC bypass and reset. Candidate selection needs only a temporary private ROM path and settings clone; no installed binary, launcher, host code, defaults or game patches need replacing. Do not pass the synthetic emulator-configured menu: the installed host must append the actual private catalog itself. Menu ROMs are raw `.bin` for this flow; the standalone sender's gzip requirement does not apply to `netdimm_menu --exe`.

The candidate base ROM is 1,461,884 bytes, SHA-256 `3ec9d4faede2fa57a1a3cf1993d5eef7e2aefcb00d7ce800432d93a819fd62a2`, serial BRP0. The local manifest's source hashes were rechecked against `native/netbootmenu/`, and its ROM hash matches. Preserve the matching debug ELF/build records; hashes of private staged evidence belong in the private run package.

| Exchange | Inspected installed host and candidate |
| --- | --- |
| Configuration | 64 bytes; `<IIIIIIIIIBBBBBBBBBBBBIII` plus four zero padding bytes; SRAM flag offset 32, calibration 36, font 48/52, players 56. |
| Catalog | 136-byte records: 128-byte UTF-8 title, four serial bytes, little-endian sorted index. IDs are regenerated each launch; do not reuse an old index without matching current filename/title/serial. |
| Select/load settings | `0x1000` selection and `0x1001` settings request carry four-byte index; ACK `0x1002`; settings data `0x1005`. |
| Save settings/config | `0x1007` settings response, empty `0x1008` ACK; 64-byte `0x1003` configuration, empty `0x1004` ACK. |
| Progress/SRAM | Eight-byte `0x1009` progress, empty `0x100A` unpack; 32 KiB `0x2003` snapshot and `0x2004` restore. Phase one keeps SRAM OFF. |

These layouts/IDs match inspected source; this does not prove real host round trips or arbitrary malformed-message safety. The host's settings serializer can emit variable patch/settings counts; broad allocation-exhaustion and malformed-count coverage remains incomplete. Do not fuzz the cabinet.

**Persistent hardware effects remain:** the native candidate explicitly reads EEPROM, clears its game-settings size and calls `eeprom_write()` on startup. SRAM OFF does not suppress that EEPROM write. Normal Naomi BIOS boot and original-menu return may also change physical settings. Host file backups/hashes cannot prove physical EEPROM/SRAM invariance or restore it. This effect must be included in the eventual live approval; no new EEPROM/SRAM restoration is authorized by this plan. The recovered original renderer source has the same clear/write behavior, but equivalence to the shipped binary and physical invariance are unproven. Existing EEPROM tools only inspect/edit local files or attached ROM settings; menu settings requests use stored/ROM/default data. The settingstrojan may write after reading and is not a verified snapshot route. No supported live physical EEPROM backup was verified in the inspected stack. Hold destructive settings/SRAM cases; a bounded renderer/control comparison can proceed after explicit approval accepting startup EEPROM effects and incomplete physical rollback. A missing snapshot is a stated limitation, not a claim that all hardware rendering must be abandoned.

## First comparison and isolated settings cases

Use the installed Python venv and inherit its PATH in subprocesses. The actual inspected target already has SRAM OFF; the prepared candidate settings clone initially matches the backed-up YAML exactly. Keep SRAM OFF throughout phase one, and verify the host-generated configured payload flag before interpreting a snapshot absence. The installed host writes any valid 32 KiB SRAM snapshot to its last-game destination even when its settings flag is OFF. OFF suppresses the candidate backup sender; it is not a host-side guard. Record any unexpected SRAM packet/file and stop. Do not toggle SRAM ON or deliberately send a malformed restore.

First observe the unchanged working menu with visible CRT and physical JVS: readability/orientation, first/last visible titles, up/down taps and repeats, scroll boundaries and usable-menu timing. Preserve current logs/configured dump before starting any menu host: `/var/log/netdimm_menu.log` is opened with `filemode='w'`, `/var/log/menudump.bin` is replaced, and menulauncher has its own truncating log. Do not invoke menulauncher just to inspect it.

After a separately approved candidate launch, the initial phase compares rendering and directional navigation only. **Omit Start entirely**, plus Test/Service/settings/save/game launch and optional debug. A short Start release sends a real game selection immediately. Source handles release before evaluating the one-second hold transition, so releasing near the threshold or during slow frames can launch a game; “hold one second then release” is not a safe settings instruction.

A later separately approved settings phase must hold Start until the settings/loading transition is visibly entered **before release**. If transition is absent, keep Start held, have the operator stop the explicitly verified host while still held and confirm it exited, then release and coordinate rollback. Do not blindly release/retry while a live host can accept selection. If a user-visible transition cannot be reliably confirmed, omit the Start settings case. Physical Test/PSW1 enters menu configuration; that is also a later case. Service/PSW2 is not an assumed universal Back button.

### Initial case matrix: one candidate upload and one original-menu return

Observe the already loaded original first, then use the same bounded cases on the candidate. Original upload/startup timing is unavailable because it is already loaded; obtaining it requires an extra explicitly approved reload/reset, outside this two-reset plan.

| Case | Bounded action and evidence |
| --- | --- |
| Visible baseline | Record original/candidate title association, orientation, font/readability at normal distance, CRT overscan/clipping and signal appearance. No Start/Test/Service. |
| Direction taps | 20 total directional taps, ten Up and ten Down, recording starting/ending highlight and unexpected skips. Stop rather than add unplanned recovery inputs. |
| Repeat | Hold Up for two seconds and Down for two seconds; record repeat onset, responsiveness and scroll behavior. |
| Endpoints | Use directional input only to reach first and last items once each; log actual input counts/duration and boundary behavior. No wrap assumption. |
| Idle | Observe for 60 seconds after navigation; record freezes/artifacts/input responsiveness. This is not memory-soak acceptance. |
| Return | Preserve evidence, stop only verified candidate host, upload/reset original menu once, confirm host wait and user-visible original menu/navigation. |

Planned target actions are exactly **one candidate upload/reset plus one original-menu rollback upload/reset**. No games, Start, saves, optional debug, settings/SRAM changes, power or startup/default tests belong to this initial phase. Original menu baseline observation adds no reset. Frame/heap/texture measurements unavailable from existing paths remain unavailable.

For an explicitly scoped settings-only case, use the private clone for reversible host persistence. Game settings have three actions: save settings and boot (also sends selection; defer), save settings and return (sends settings and waits for ACK), and Back (discards local changes). Menu configuration has Save and exit and Exit without saving; both control paths need observation, but do not change region/player/calibration/SRAM for an initial parser/save check. A harmless reversible sound/display setting may be agreed, changed in the clone, read back, then returned to its baseline. A game-settings save can change the clone's EEPROM/force-settings metadata even without booting; keep that private and do not later launch a game from the modified clone unintentionally. Never enable new patches. Installed host code can apply already enabled patches/forced EEPROM on a game launch: an eventual launch case needs review of that exact game's clone entry, not just this menu test.

No game launch is part of preparation. The private package lists previously configured IDs and a short list from the prior catalog, with filenames/serials only privately. Their old presence is not proof that files are still installed/unchanged or that a game is safe to launch. Reconcile the newly generated configured payload, current enabled catalog row, exact ROM file/hash, patches and force-settings before choosing one separately approved game.

## Diagnostics, stopping and explicit rollback

Default comparison omits `--debug-mode` to match normal behavior. An optional second launch can enable its FPS/frame-draw overlay; this is another reset and separately reviewed case. The flag also reaches game EEPROM trojan debugging on applicable game launches, so it is not an overlay-only global guarantee. Overlay FPS/draw time and host logs do not expose Naomi heap/texture trends; memory/soak acceptance remains unavailable unless a reviewed measurement method is added.

Capture private host console/logs, configured dump/hash/config flags, base ROM and matching ELF/build records, timestamps for sender start/completion/usable menu, input sequence, observed screen/error codes and outcome. Preserve evidence before any retry. Manual visual timings are separate from upload and playable-game timing. No retry, persistent auto-relaunch, phone launch, optional control/card reconfiguration or power/startup test should run concurrently.

Stop on wrong game/title/ID, unexpected settings/SRAM effects, missing ACK/timeouts, frozen controls/rendering, transfer failure or unexpected cabinet behavior. Preserve evidence, confirm no transfer is active and stop only the explicitly tracked candidate menu-host PID. Then launch the installed original base menu through the same installed host with normal original settings and without `--exe`/`--debug-mode`; retain the usual host so future menu edits persist normally. The candidate settings clone is discarded from use, not copied over real YAML. Installed defaults remain unchanged. Never kill by broad process name or automatically send a game.

Rollback is a separate explicit transfer/reset. It is complete only after successful host transfer, waiting-for-selection evidence and user-confirmed visible original menu/JVS behavior. Hash/owner/mode checks for original files and absence of unexpected SRAM files support host restoration; they do not establish physical EEPROM restoration. Keep private candidate clone/logs and preflight backups until review. If the intended return is a game or startup/power behavior instead of the original menu, prepare that exact case separately.
