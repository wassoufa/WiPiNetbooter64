# Start here: AI handoff and current state

State reviewed **2026-11-13 Australia/Melbourne**. This is the current-state index; [the roadmap](roadmap.md) owns sequence/gates, [the runtime plan](native-runtime-test-plan.md) owns capture and acceptance, and [the blank result template](templates/runtime-test-result.md) owns individual observations. Recheck Git/PR/deployment records on resuming; do not assume a source merge installed anything.

## Source identity

| Item | Reviewed identity |
| --- | --- |
| Maintained fork / `origin` | [wassoufa/WiPiNetbooter64](https://github.com/wassoufa/WiPiNetbooter64); push fork work here |
| Parent / `upstream` | [cassianoperin/WiPiNetbooter64](https://github.com/cassianoperin/WiPiNetbooter64), ultimately chunksin's WiPiNetbooter |
| Installed system last inspected | `wipi 0.22-0`, Debian 13 arm64; public upstream is older, not an exact installed-package source mirror |
| [PR #1](https://github.com/wassoufa/WiPiNetbooter64/pull/1) | **Merged** 2026-11-12 12:58:01 UTC; source merge `f497c5847d1cc70f495451827324d445c08f9197` on `master` |
| [PR #2](https://github.com/wassoufa/WiPiNetbooter64/pull/2) | **Open draft** native text baseline; reviewed implementation head `f98bd462e919491f1ed19507b58ad4f0b8c66524` on `codex/native-menu-baseline` |
| Renderer source | [hmofet/netboot](https://github.com/hmofet/netboot/tree/6ccbfdd000e705678ee422ebe972c2fccce40693/homebrew/netbootmenu) `6ccbfdd000e705678ee422ebe972c2fccce40693`; file provenance in [upstream.json](../native/netbootmenu/upstream.json) |
| libnaomi | [DragonMinded/libnaomi](https://github.com/DragonMinded/libnaomi/tree/c840eb85384725182392ee3361706e80ae4ca4c0) `c840eb85384725182392ee3361706e80ae4ca4c0` |
| Builder base | `rattboi/naomi-build@sha256:f8fb420595d945d3379f51f2675e6390e4decbb622b8c8bea79cc8eeeee2f83e` |

The implementation head above is a dated checkpoint, not a promise that future documentation commits leave `HEAD` unchanged. Use `git status --short`, `git branch --show-current`, `git rev-parse HEAD` and `git log -5 --oneline` before editing. Read [AGENTS](../AGENTS.md), [the fork baseline](fork-baseline.md), [loading-status behavior](loading-status.md) and [native build/proof details](../native/README.md). The user's resource-cleanup preference is Sol editing project files and Astra reviewing when available; report a missing review rather than implying it occurred.

## What is proven and what is pending

| Area | Evidence / limit |
| --- | --- |
| Existing cabinet baseline | OSM eight-field default-save correction and ordinary per-target upload guard passed cabinet tests. Preserve Single Boot, custom game entries and optional control/card integrations. |
| New phone loading status | Offline concurrency/failure/status/PHP/serialization checks passed. PR #1 is merged source. The new status enhancement is **not installed** and hardware acceptance is pending; the cabinet retains the previously tested fixes. |
| Native build | Cross-build, ROM structure validation, configuration/host layout and fake-SRAM checks passed. A settings/parser and upload-status-helper audit fixed cleanup/ownership failures; exercised host paths showed no detected leaks. PR #2 includes the Python `sbin/piforce/upload_status.py` initialization-failure cleanup fix beyond PR #1, as well as native changes; sender/menu-host scripts and launcher selection are unchanged. See [exact fixture coverage and sanitizer command](../native/README.md#build-and-local-proof). |
| Native unknowns | Allocation exhaustion/arbitrary malformed counts, font/texture resource ownership on target, settings/game protocol exchange, real battery SRAM and long soak remain unverified. Physical JVS directional taps/holds/endpoints and 60-second idle now have limited user-confirmed Phase A evidence. Balanced fixture counters/sanitizers are not proof of every runtime allocation or a leak-free cabinet. |
| Runtime/deployment | Native candidate has now rendered and navigated in an isolated interpreter-only Flycast run. It also completed an approved temporary [Naomi Phase A comparison](results/2026-11-13-naomi-phase-a.md) with user-confirmed directional navigation/60-second idle, then was replaced by the original shipped menu. It is not selected persistently. Original menu binaries on the Pi are unchanged by this work. No new native artwork or video is implemented. |
| Emulator preparation | Synthetic fixture checks and official Flycast v2.7 local build/isolated CLI help passed. An authorized own-board BIOS capture completed: two equal full reads and verified private copy, recognized by Flycast's known BIOS CRC table. BIOS bytes/identity/hash stay private. Two local emulator launch attempts then exited 133 at a pre-ROM SH4 memory-mapping assertion; neither attempt executed the candidate. A supported interpreter-only fallback then built successfully with `TARGET_NO_REC` and GDB OFF; it subsequently loaded the private BIOS and synthetic candidate, rendered the list and passed bounded navigation/scroll checks, then quit with exit 0. See the [dated result](results/2026-11-13-native-emulator.md). Stock raw-BIN E3 host messages remain unsupported; no bridge implemented. See [readiness/build evidence](native-runtime-test-plan.md#stage-e-isolated-emulator-preparation-and-baseline). |
| Design preview | [Browser layout preview](previews/illustrated-osm.html) demonstrates a five-entry concept; it is not native runtime proof. |

## Candidate artifact and reproducibility record

**Post-Phase-A source change (2026-11-13, not yet run on emulator or Naomi):** `main_menu` in `screens.c` now treats a Start release on or after the 1-second hold frame as a settings request, never a game launch. Previously the release was handled before the hold check in the same frame, so a release at the threshold or during a slow frame launched the game. This deliberately differs from the original menu's inherited behaviour. The rebuilt base is now 1,461,916 bytes, SHA-256 `45ef4f205449bb8cbae7ed74c8d064e6140de4b9ac4469b8c420c7941df1a035`. The Phase A-tested `3ec9d4fa…` artifacts below are preserved outside the checkout in `../wipi-fork-out-phase-a-backup/`. The record below describes the Phase A artifact.

The rebuilt, **unconfigured base** `native/out/netbootmenu.bin` is 1,461,884 bytes, serial `BRP0`, date `2026-11-13`, main/test entry points `0x0C021000` / `0x0C021004`.

```text
SHA-256 3ec9d4faede2fa57a1a3cf1993d5eef7e2aefcb00d7ce800432d93a819fd62a2
local builder image sha256:07752cb87e3705adf329c281a0b94079275cec6fef124701880913b2b7799967
compiler sh-elf-gcc 9.3.0
```

The existing `native/out/SHA256SUMS` and `manifest.json` agree with the base ROM hash above. Check the bytes again before use (`shasum -a 256 native/out/netbootmenu.bin`) and compare every `source_sha256` entry in the manifest with `native/netbootmenu/`. Keep the manifest, debug `naomi.elf`, `compiler.txt`, `elf-header.txt`, `python-packages.txt` and `builder-image-id.txt` with private runtime evidence. These ignored local artifacts must be rebuilt if missing; the full archive URLs/hashes are in [sources.json](../native/build-env/sources.json), explicit Python pins in [requirements.txt](../native/build-env/requirements.txt), and the build procedure in [native/README](../native/README.md#build-and-local-proof). Compilation is isolated/offline after dependencies are acquired; the initial builder setup needs network access. APK packages and transitive Python dependencies are not all pinned to immutable versions, so retain the actual image/package record. The current rebuilt hash has not been proven by two clean identical rebuilds.

The base ROM is **not a standalone emulator fixture**. `config.c` reads a host-appended configuration at `0x0D000000`. The real host's [serializer](../sbin/piforce/dm_netboot/scripts/netdimm_menu.py) appends 64 configuration bytes, 136 bytes per game and optional fallback font with `add_or_update_section` before sending. The new [offline fixture generator](../native/README.md#offline-emulator-fixture) uses that helper without importing/running the live host entry point. It generates only invented titles/serials, disables SRAM and mutes sound. Original executable bytes and base ROM are preserved. The inspected Flycast v2.7 raw-BIN path does not supply the required host-message bridge; an isolated adapter or another verified path is needed before claiming Start/settings round trips. See the [pinned source evidence](native-runtime-test-plan.md#stage-e-isolated-emulator-preparation-and-baseline).

Current synthetic output, generated and validated offline on 2026-11-13:

| Artifact under ignored `native/out/emulator/` | Bytes | SHA-256 |
| --- | --- | --- |
| `synthetic-config.bin` (64-byte config + 26 × 136-byte records) | 3,600 | `d86fba07ae86774564609af88af3b003df708a25c88e69aa5b5b48eed65d670e` |
| `configured-menu.bin` | 1,465,484 | `153d4ca05db9099f358c514e1ee91fb970f647080b67eb39e902c2a6c09db944` |

`fixture-manifest.json` records flags, calibration, IDs/titles/serials, section file/load bounds, base and output hashes and generator identity. `SHA256SUMS` also covers that manifest. Preserve the matching base/debug/build records above with it. Generation is not boot, rendering, navigation or settings evidence. The existing startup EEPROM write still occurs inside an emulator; keep emulator persistence isolated.

## Own-board BIOS capture and explicit menu return

On 2026-11-13 the user approved a coordinated temporary helper launch, capture and original-menu return after read-only preflight and verified private backup. The [dedicated BIOS helper/client](../native/biosdump/README.md) completed one capture exit 0 in about 27 minutes 18 seconds: two full volatile 2 MiB reads matched, and the copied private image matched the capture hash and a known Flycast BIOS CRC. Firmware bytes, identity/hash and target details remain private. Six synthetic protocol/output/deadline tests also pass.

The helper transferred/reset once; afterward the root agent retransferred/reset the original shipped menu once through installed `netdimm_menu` with an exact settings clone (SRAM already false). Host evidence reached waiting for ROM selection. After confirming the installed YAML was unchanged, the temporary settings path was atomically replaced with an alias to the original YAML so future normal menu edits persist normally; no additional upload/reset was needed. Installed CSV/settings/menu binary hashes were unchanged; SRAM directory remained README only. CRT was off at that capture checkpoint. The user later confirmed the original menu visually but found both players' navigation inactive, as recorded below; physical EEPROM/SRAM invariance remains unproven. The native candidate was not deployed. Existing `/opt/wipi64-venv/bin/python` and inherited venv PATH supplied dependencies; no installation/default changes were made.

The [runtime plan](native-runtime-test-plan.md#stage-e-isolated-emulator-preparation-and-baseline) and [local build recipe](flycast-local-build.md) separate the failed JIT startup attempts from the successful interpreter-only [rendering/navigation observations](results/2026-11-13-native-emulator.md). E3 host round trips and memory soak remain unverified. The later hardware Phase A provides limited directional/held-repeat/idle observations, not full physical acceptance.

## Resume work and preserve evidence

The bounded [Naomi Phase A comparison](results/2026-11-13-naomi-phase-a.md) is complete with original-menu return. Review its limited results and separately scope remaining Start/settings/game/SRAM/Single Boot/soak cases; stock raw-ROM Flycast still cannot supply E3 host messages. The Start release-before-hold transition hazard remains unchanged. No further live deployment, artwork/video or phone-status change is implied. Follow [the runtime plan](native-runtime-test-plan.md) and preserve independent approval boundaries.

Keep raw captures, real settings, private addresses, BIOS/ROMs, SRAM and cabinet media outside the checkout, or under ignored `native/out/runtime-tests/`. Commit only synthetic fixtures and reviewed/redacted summaries; do not add private evidence to an issue/PR automatically. At handoff, record source/ROM/config identity, each case outcome and evidence ID, open bugs, exact last action, rollback state and the next bounded action. Use [the result template](templates/runtime-test-result.md); absent diagnostics must be marked unavailable with a reason, never inferred as healthy.

When state changes, update this file's date, source/artifact identities and acceptance rows. Keep the implementation/proof detail in its source document, the work order in the roadmap, and case evidence in result records. There is no need to copy a fresh status narrative into every README.

Current handoff checkpoint: the isolated emulator is closed. The approved Naomi Phase A comparison completed, and the original shipped menu/controls were returned and user-confirmed. Its normal installed host remains active with real YAML; candidate is not selected persistently. PR #2 remains draft. Private logs/configured payloads/settings/photos stay outside tracked source.

## Naomi Phase A completed: bounded navigation only

The user explicitly approved the reviewed two-reset comparison, including startup EEPROM effects/incomplete physical rollback. After original navigation recovered following the user's manual Naomi restart, original and candidate cases were reported normal: ten Up/ten Down taps, two-second Up/Down holds, endpoints; both 60-second idle observations were stable. The candidate's familiar text-list appearance was expected, not a blank/error failure. See the [dated redacted hardware result](results/2026-11-13-naomi-phase-a.md).

The installed host temporarily used `--exe` with the verified raw candidate and regular exact SRAM-OFF clone. Host-generated candidate payload was 1,485,340 bytes; configuration/catalog matched the original and candidate CPU bytes were preserved. This is host/staged-file identity plus upload/user evidence, not target readback. The candidate host was verified and stopped with TERM/pidfd after evidence preservation; the original was uploaded through the installed host using real YAML. User confirmed original menu and controls work. Exactly two AI upload/reset cycles occurred for this comparison; no games, Start, Test/Service, saves, SRAM enable, debug, AI power or startup/default actions occurred.

Installed main menu/YAML/CSV hashes and clone remained unchanged, SRAM directory README only. Post-run verification matched all 24 installed non-log regular files from the 34-member preflight archive on SHA-256, numeric UID/GID and modes; expected changing logs were excluded. A private 2.7 MiB live-session evidence archive is retained. Physical EEPROM/SRAM invariance remains unproven: candidate startup clears/writes game EEPROM and host/menu return does not restore physical EEPROM. No target heap/texture or sustained-soak proof exists. Original upload/startup timing was unavailable because it was already loaded.

The earlier original both-player input failure preceded candidate staging. Entire pre-BIOS/restored original configured payloads matched byte for byte. User restart recovered cursor input but caused the nonpersistent host to exit, consistent with source; no JVS root cause was established. This historical recovery is separate from the successful candidate comparison and return.

N0 readiness included 22 source hashes/base ROM/exact clone checks and a fresh 34-member backup with disposable offline recovery rehearsal matching bytes/hashes/numeric ownership/modes; no installed restore was performed. Private clock samples had maximum round-trip 0.045 seconds and no clocks changed. Astra reviewed readiness, not these user-observed runtime results.

Next bounded action: review the completed limited result and separately scope remaining tests; post-run metadata/private evidence checks are complete. Settings/Start/ACK/save/gameplay, SRAM association/restore, Single Boot and memory-soak cases remain separately gated. The source Start release-before-threshold hazard is unchanged; no blind hold-and-release settings test. No new live action or artwork/video/phone deployment is implied.
