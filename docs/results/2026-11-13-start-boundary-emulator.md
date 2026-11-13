# Start boundary: partial isolated emulator evidence

Observed 2026-11-13, Australia/Melbourne (UTC+11). The Start-fix candidate reached both the launch animation and the settings-fetch screen, but nominal one-second hold behavior remains unresolved in the interpreter. This is not settings/launch round-trip or Naomi acceptance. See the [current handoff](../ai-handoff.md), [roadmap](../roadmap.md) and [runtime plan](../native-runtime-test-plan.md).

## Run identity

| Field | Recorded identity |
| --- | --- |
| Source checkpoint | `aa4bed31e4c81b4b64cc1ce93b994cdcf800d4b0`, branch `codex/native-menu-baseline`; Start fix `633d284`; production source unchanged during this check |
| Base ROM | 1,461,916 bytes; SHA-256 `45ef4f205449bb8cbae7ed74c8d064e6140de4b9ac4469b8c420c7941df1a035` |
| Configured synthetic ROM | 1,465,516 bytes; SHA-256 `8635542a16f90acf6eb3fcafa4a800059baaab80f93387670d3be60b4c26ab62` |
| Synthetic configuration | SHA-256 `d86fba07ae86774564609af88af3b003df708a25c88e69aa5b5b48eed65d670e`; invented titles/IDs, SRAM disabled, sound muted |
| Matching debug ELF | SHA-256 `e9b14a2f976c8506a7bf7889687f5758700020ee63e36b19915222a9cb30638d` |
| Flycast | v2.7 source `5aa091fde632fb332c8d8c34e280d62dc951954c`; supported interpreter-only build, GDB disabled; executable SHA-256 `2b8dcf7a8670046d3b98b56f647e52af3da8445eddf7a05545b00713c4f1fcf6` |
| Build provenance | [Pinned build recipe](../flycast-local-build.md#supported-interpreter-only-fallback-after-startup-failure); matching manifests/compiler/package records retained with the local evidence bundle |
| BIOS/persistence | Private own-board BIOS; one new private profile populated once with a BIOS-only copy, then reused across all four cases with synthetic EEPROM/nvmem retained; firmware bytes/identity remain private |
| Input/video | CUA `App.pressKey(Return, {durationMs})`, Return/Start; OpenGL; observed screen captures; no host-message bridge |
| Hardware scope | Naomi OFF per user; no SSH, Pi action, upload, reset or cabinet test in this check |

The earlier Phase A-tested base (`3ec9d4fa…`) and its configured ROM/ELF are different artifacts. Their [bounded directional/idle acceptance](2026-11-13-naomi-phase-a.md) does not transfer to this candidate.

## Case outcomes

An inherited-profile attempt from 16:44:01 to 16:48:15 displayed a blank view with an emulator overlay; the native menu was not seen. A subsequent fresh private subdirectory with BIOS-only contents rendered the menu. The blank cause is not established; this observation does not diagnose persistence corruption or a ROM defect. The earlier locked-screen attempt also supplied no input outcome.

The following four cases shared the same newly isolated profile at `work/flycast-runtime/start-fix-clean-20261113/`, initialized once with a BIOS-only copy; synthetic EEPROM/nvmem persisted between runs. Each process exited 0, captured with shell `pipefail`. Input used CUA `App.pressKey(Return, {durationMs})`. Intervals below come from Flycast SDL received key-down/up events, not guest control polls; they do not measure when the native menu sampled input or guest hold duration.

| Case | Host key interval (UTC+11) | Requested / logged elapsed | Observed result / assessment |
| --- | --- | --- | --- |
| Short Start | 16:50:03.222–16:50:03.424 | 200 ms / 0.202 s | List flyaway/launch animation, then `Communication Error!`. Consistent with the launch route without a host bridge; no real selection delivery or gameplay proven. |
| Nominal long hold | 16:52:07.186–16:52:08.774 | 1,500 ms / 1.588 s | Also list flyaway/launch animation, then error. Unexpected relative to the requested wall duration; timing unresolved. This is not a long-hold pass or a diagnosed source bug. |
| Longer hold | 16:54:02.081–16:54:10.513 | 8,000 ms / 8.432 s | Only the error screen was captured. Prior route is ambiguous; neither launch nor settings entry is established by that capture. |
| Settings-path observation | 16:56:02.207–16:56:05.360 | 3,000 ms / 3.153 s | `Fetching game settings...` captured, followed by the expected no-host error. Settings-fetch route observed; ACK/data, edit, Back and save exchange unavailable. |
| Near-one-second sweep | Not run | — | A 0.95/1.00/1.05 s host-wall sweep would not establish the exact guest-time boundary with the present diagnostics. |
| Final exit | After the final case | Four isolated-run exits 0 | Flycast closed; GUI closure confirmed. No continuing emulator run. |

## Deterministic proof and timing limits

The new host fixture extracts the actual production `main_menu` from `screens.c` with fake controls, time, UI and messages. Short releases at 0.125 and 0.999999 guest-source seconds send exactly one selection; release at exactly 1.0, 1.000001 and 1.75 seconds enters settings without selection, including a slow frame crossing the threshold. Continuous hold, control locking, reinitialization and stray release checks pass. All four native tests pass normally and with AddressSanitizer/UndefinedBehaviorSanitizer. Restoring the pre-fix release branch in memory makes the new settings/no-selection assertion fail. See [fixture details and commands](../../native/README.md#build-and-local-proof).

The native threshold uses guest profile microseconds sampled at frame start. Elapsed time between Flycast SDL key events is not guest elapsed time or evidence of when input was sampled. `CPU_RATIO=8` alone is not a measured conversion. Astra reviewed the fix and fixture without actionable defects or added allocation behavior; the timing analysis remains inconclusive. No production change was made to compensate for these observations.

Host SDL input-event logs are present; no guest input-recognition trace, guest-clock correlation, FPS history, target heap/texture telemetry or soak measurement was collected. The stock raw-BIN route lacks the E3 host-message bridge, so a communications error is not successful ACK/settings/save/gameplay exchange. Neither source fixture proof nor interpreter observations establish exact emulator or physical JVS timing.

## Evidence and next gate

Private raw logs are retained outside the repository in `work/flycast-runtime/start-fix-clean-20261113/`. The ignored `native/out/runtime-tests/start-fix-20261113/` bundle retains matching build/runtime evidence; selected user-facing captures are under outer `outputs/start-fix-emulator/`. The private bundle index is `evidence-index-private.json`; it includes logs and matching artifacts. Eight screenshots are in the outer output directory. The primary agent owns the evidence manifest. Do not publish firmware, profiles, real settings or unreviewed raw evidence.

Next bounded work: investigate guest-clock and input-delivery timing in the isolated emulator, using minimal reversible diagnostics if needed, before accepting a nominal one-second hold. Preserve the unexpected 1.588 s wall-time outcome and the ambiguous 8.432 s capture. Settings ACK/Back/save, gameplay, SRAM, Single Boot and memory soak remain open. A later Naomi settings comparison needs separate concrete approval; Naomi remains OFF. Keep PR #2 draft and defer artwork/video.

## Event-only probe: emulator speed explains the timing (2026-11-13 ~18:16 AEDT, Claude)

Two runs of the event-only diagnostic ROM (`native/emulator/build-start-event-diagnostic.py`, configured SHA-256 `d5ee81b0f7b5a28066de6b4a637f153219a36f35fdf1078e49c9ad885f94bf28`), interpreter Flycast, with framebuffer emulation enabled in the reused isolated profile. The probe draws nothing until a route is decided. Return was held with a CGEvent key helper while Flycast was frontmost; host intervals are Flycast SDL `BUTTON down/up 8` log times.

| Host hold | Guest frames | Guest hold: animation counter / independent `profile` timer | Route | Selection sends |
| --- | --- | --- | --- | --- |
| 1.516 s | 31 (903→934) | 0.516866 s / 0.517139 s | 1 = launch, list flyaway | 1 |
| 3.483 s | 90 (899→989) | 1.517252 s / 1.518010 s | 2 = settings, decided at 1.000425 s before release; `Fetching game settings...` shown | 0 |

Assessment: the animation counter and separate profiler interval agree within 1 ms in these samples, about 16.7 ms per guest frame. The clean launch sample measured about 0.517 guest seconds during a 1.516 s host interval: the interpreter was slower than wall time. This supports slowdown as an explanation for the earlier outcomes; those earlier runs lacked a guest trace, so their exact timings cannot be reconstructed. No production clock change is justified by this evidence. The longer sample chose settings at 1.000425 guest seconds with zero selection-branch calls. Its interval through release includes post-decision overlay work, so the resulting roughly 44% ratio is not a clean pre-decision speed measurement. Neither ratio is a fixed conversion for future tests. Counters describe branch calls, not delivered or acknowledged packets.

Reproduction correction from primary-agent log review: both logs contain an **invalid combined `-config` warning** for the debug/framebuffer argument. That argument was ignored. The isolated `emu.cfg` has `rend.EmulateFramebuffer = yes`, and the captures show its CPU-written overlay. Use separate, fully qualified arguments for future runs:

```sh
-config 'config:Debug.GDBEnabled=no,config:Debug.GDBWaitForConnection=no' \
-config 'config:rend.EmulateFramebuffer=yes'
```

The interpreter executable was compiled with GDB disabled; the malformed runtime argument does not establish runtime overrides. Preserve profile state as well as the command line. The primary agent checked both captures, SDL event intervals and diagnostic artifact hashes against this record; the attempted additional Claude CLI review was unavailable due its usage limit. Astra's earlier bounded source review does not establish target runtime acceptance.

Limits: two event-probe runs; the canonical ROM was not rerun during that probe session. The earlier canonical 1.5 s repeat remains a recorded launch observation. Interpreter speed does not measure Naomi timing. Physical JVS timing, settings ACK/Back/save and everything in Phase B1 remain open. Captures are in outer `outputs/start-timing-emulator/probe-*.png`; logs are `event-probe-1500ms-claude.log.gz` and `event-probe-3500ms-claude.log.gz` in outer `work/flycast-runtime/start-timing-20261113/`. Flycast was closed after each run. No diagnostic belongs on hardware.
