# B4 offline memory-diagnostic readiness, 2026-11-14

**Offline readiness PASS; cabinet capture and soak pending.** Sol implemented an isolated diagnostic builder, bounded sampler and capture decoder, with focused tests. Astra reviewed ownership/failure handling and independently checked the diagnostic tests. The original menu, canonical source/pins, installed Pi software and cabinet were untouched. No SSH, NetDIMM upload or physical power action occurred in this stage. PR #2 stays draft. See the [implementation/use notes](../../native/diagnostics/README.md) and [B4 plan](../native-memory-soak-plan.md).

## Evidence and limitations

| Check | Observed result / boundary |
| --- | --- |
| Pinned allocator API availability | Actual SH-4/newlib headers compile `mallinfo()` and pinned libnaomi `ta_texture_mallinfo()`; full diagnostic links successfully |
| Standalone allocator runtime probe | Isolated interpreter Flycast, static report observed via CUA: a 4,096-byte heap request changed live bytes 27,704 → 31,808 → 27,704; arena remained 32,772. A 32×32×16-bit managed texture changed live bytes 0 → 2,048 → 0; arena/free after release 9,437,184. Heap overhead is included. This verifies API response in that emulator, not Naomi memory behavior |
| Sampler/capture tests | Four tests compile actual sampler C against target-shaped mocks and exercise quiet/held-input/transition gates, queue activity/races, one-time calibration, unsupported save departure, clock/send failures, timer cleanup, record cap and decoder malformed/missing/duplicate/invalid/changed-game/trailing-idle cases |
| Existing native regressions | Four existing configuration/SRAM/settings/Start tests passed; canonical source/pin unchanged |
| Sanitizers | Four diagnostic tests passed host ASan/UBSan. macOS leak sanitizer was unsupported; corrected run used `detect_leaks=0`. This is not leak-sanitizer proof or real allocator ownership coverage |
| Offline cross-build | Existing pinned builder, networking disabled, read-only source and temporary build storage; artifact/manifest hashes verified |
| Synthetic diagnostic ROM | Interpreter Flycast rendered the invented list; one Down moved highlight from “A” to “Amber Circuit.” No Start/settings attempted. This is bounded rendering/input evidence, not settings telemetry capture |
| Host-style capture/decoder | Actual sampler fixture output and logger-prefixed variants decoded offline; invalid/incomplete inputs failed. Mocked capture is explicitly labelled, not presented as target values |
| Review | Astra concrete review passed after unsupported settings-departure and input-gating fixes; builder now guards screen constants/patch anchors. Astra also rehashed artifacts/canonical identity and checked the final documents against recorded probe values. Root owns CUA observations and process/log verification; Astra did not repeat those observations. No target soak review/acceptance is implied |

Both isolated emulator processes were identity-checked and stopped after observations; their debug logs were compressed and verified. Private standalone probe source, Makefile, ROM/ELF, launch records and observed result are retained outside the checkout. No BIOS material or raw emulator evidence is committed.

## Artifact identity

| File under ignored `native/out/memory-diagnostic/` | Bytes | SHA-256 |
| --- | --- | --- |
| `diagnostic-base.bin` | 1,464,452 | `4258fa6e764a5e774a44999ce12628becbe2237648c35488a5bf205d1caa49f2` |
| `configured-diagnostic.bin` | 1,468,052 | `85a7f5dd30872f8a55416a512e0154de93f8516f1bbf89b7c69844eb328012c1` |
| `diagnostic.elf` | 5,758,996 | `88474e41652193db4e7cf8dec1077614be9a6005383157cd4680fcde7820db9e` |
| `source.patch` | recorded in manifest | `3c9879e9e94f4824a638e30315d08ea9d4ac588cf717d17398300a9a76d0d8b7` |

Builder image ID is retained beside the manifest/compiler/package record. The manifest covers 22 canonical source files, six instrumented copied files and generated artifact hashes. Canonical bare SHA-256 remains `45ef4f205449bb8cbae7ed74c8d064e6140de4b9ac4469b8c420c7941df1a035`; it was neither rebuilt over nor repinned. Do not send the synthetic configured diagnostic to the cabinet. A later approved run uses the bare diagnostic plus a freshly inspected installed host/catalog/private clone, producing another configured identity.

Ignored offline evidence is under `native/out/runtime-tests/b4-memory-offline/`: build/native/diagnostic/sanitizer logs and mocked capture/decoder provenance. External private probe/runtime directories are indexed in the outer handoff. Local artifacts must be rebuilt/reverified if missing; source merge does not deploy them.

## Next gate

Prepare a fresh cabinet comparison package, confirming target capture/calibration before measured cycles, with new installed/process/settings/catalog checks, verified backups/recovery and explicit original return. The [plan](../native-memory-soak-plan.md) proposes two warm-up plus 20 measured open/discard cycles and 15 minutes idle; operation count, current cabinet readiness, host/guest duration and physical EEPROM effects still require concrete execution review/approval. This offline result does not authorize that upload.

Target heap/texture trends, actual log completeness, diagnostic timing cost, physical EEPROM/SRAM invariance/rollback, cold-host settings persistence, Single Boot and real battery-SRAM association/restore remain unverified. Metrics cover their allocators, not all memory or fragmentation. No leak-free claim follows. Phone acceptance remains undeployed and separate; artwork/video remain gated.
