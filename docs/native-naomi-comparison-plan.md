# Prepared Naomi text-menu comparison (N0)

This is a reviewable plan, not authorization to launch it. Preparation used read-only Pi access/backups only; no target command, process change, upload, reset or game launch was performed. The native candidate has not been deployed. The existing [runtime plan](native-runtime-test-plan.md#stage-n-approved-backed-up-naomi-comparison) owns acceptance; the [handoff](ai-handoff.md) owns current status. The user requested preparation only. Sol prepared this package and Astra completed independent review with no remaining blocking findings for user approval; this is readiness review, not runtime acceptance. User approval of the concrete live scope remains pending. A fresh read-only private backup now includes original main/dark/light variants, host/wrappers/transports, settings/catalog/SRAM and logs with identities/owners/modes verified; no target operation was used for that preflight.

## Readiness proof and next action

The 22 candidate source-file hashes, base ROM hash and exact private settings clone were reverified. A fresh private archive records 34 members with SHA-256, numeric UID/GID and modes. A disposable recovery rehearsal using the existing `python:3.12-slim` image `sha256:dd29372629eeba2dd003fd9e9d35a5b8236c44727875a0364254b5127af88e65`, networking disabled, read-only container and temporary restore filesystem matched all 34 members' bytes/hashes/owners/modes against the manifest. This was an isolated archive recovery rehearsal, not restoration of installed files or physical EEPROM/SRAM.

Read-only host/Pi clock samples were retained privately; the maximum sampled round-trip was 0.045 seconds and no clock was changed. These samples support timestamp interpretation, not a claim of synchronized clocks or measured cabinet timing. The candidate package remains local and has not been staged on the Pi. Only preparation is authorized.

The next bounded action is user review of **Phase A: visible original baseline plus candidate rendering/directional navigation and explicit original-menu return**, agreement on a visible CRT/JVS window, and explicit acceptance of startup EEPROM clear/write with incomplete physical rollback. The concrete two-reset scope is below. Do not stage, stop the active host, upload/reset or begin cases before that review/approval. Astra review passed for this corrected preparation package; settings/SRAM/game cases are separate.

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
