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
| Native unknowns | Allocation exhaustion/arbitrary malformed counts, real rendering/font ownership, physical JVS, NetDIMM exchange, real battery SRAM and long soak are unverified. Balanced fixture counters/sanitizers are not proof of every runtime allocation or a leak-free cabinet. |
| Runtime/deployment | Native candidate has **not run in an emulator or on Naomi**, and is not selected by the installed launcher. Original menu binaries on the Pi are unchanged by this work. No new native artwork or video is implemented. |
| Emulator preparation | Offline synthetic fixture generator implemented; four identity/layout/serializer checks passed. No Flycast/RetroArch installation found. Flycast v2.7 remains a source-inspected candidate; raw Naomi ROM loading requires a BIOS the user does not have. No emulator installation/build/run or BIOS acquisition occurred. Its stock raw-BIN cartridge path returns fixed DIMM register values and ignores writes, so protocol round trips need an isolated adapter. See [readiness details](native-runtime-test-plan.md#stage-e-isolated-emulator-preparation-and-baseline). |
| Design preview | [Browser layout preview](previews/illustrated-osm.html) demonstrates a five-entry concept; it is not native runtime proof. |

## Candidate artifact and reproducibility record

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

## Resume work and preserve evidence

The next open step is [roadmap milestone 1](roadmap.md): resolve emulator readiness, including a lawfully available BIOS, and establish which input/debug/message paths are supported. The isolated configuration fixture is ready. Then follow [the emulator-to-Naomi plan](native-runtime-test-plan.md). Do not deploy a binary simply because it built. An approved hardware comparison needs a concrete diff, verified backup/rollback and agreed test window; this preparation did not access the Pi or launch a game.

Keep raw captures, real settings, private addresses, BIOS/ROMs, SRAM and cabinet media outside the checkout, or under ignored `native/out/runtime-tests/`. Commit only synthetic fixtures and reviewed/redacted summaries; do not add private evidence to an issue/PR automatically. At handoff, record source/ROM/config identity, each case outcome and evidence ID, open bugs, exact last action, rollback state and the next bounded action. Use [the result template](templates/runtime-test-result.md); absent diagnostics must be marked unavailable with a reason, never inferred as healthy.

When state changes, update this file's date, source/artifact identities and acceptance rows. Keep the implementation/proof detail in its source document, the work order in the roadmap, and case evidence in result records. There is no need to copy a fresh status narrative into every README.
