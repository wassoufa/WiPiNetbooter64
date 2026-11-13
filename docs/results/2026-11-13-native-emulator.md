# Native text menu: bounded emulator observations

Historical pre-Phase-A observation on 2026-11-13, Australia/Melbourne. Later records: [bounded Naomi Phase A and original-menu return](2026-11-13-naomi-phase-a.md), then [partial Start-fix emulator evidence](2026-11-13-start-boundary-emulator.md). This is a rendering/navigation result, not cabinet acceptance, a performance benchmark or a leak-free soak. Read the [handoff](../ai-handoff.md), [roadmap](../roadmap.md) and [runtime plan](../native-runtime-test-plan.md) before continuing.

## Reproduce the environment

Use the [pinned Flycast build recipe](../flycast-local-build.md#supported-interpreter-only-fallback-after-startup-failure). The ordinary JIT build and runtime-interpreter option both failed before BIOS/ROM load at the SH4 memory-layout assertion. The separate supported `TARGET_NO_REC` build, with GDB disabled, loaded the BIOS and ROM successfully. No assertion was removed and no emulator message bridge was added.

| Item | Identity |
| --- | --- |
| Flycast source | v2.7, `5aa091fde632fb332c8d8c34e280d62dc951954c`, plus the recorded two build-only CMake changes |
| Interpreter executable SHA-256 | `2b8dcf7a8670046d3b98b56f647e52af3da8445eddf7a05545b00713c4f1fcf6` |
| Configured synthetic ROM SHA-256 | `153d4ca05db9099f358c514e1ee91fb970f647080b67eb39e902c2a6c09db944` |
| Synthetic configuration SHA-256 | `d86fba07ae86774564609af88af3b003df708a25c88e69aa5b5b48eed65d670e` |
| Matching debug ELF SHA-256 | `1140b82d970918a2bcfe6d2d9b6078e35e9c7c4d20e4801731579f4f90dc83d7` |
| BIOS | Own-board private capture, two complete equal 2 MiB reads, recognized by Flycast's BIOS CRC table; bytes and identity retained privately |
| Input/video | Default SDL P1 keyboard, arrows; OpenGL; native captures 640 × 480 |
| Isolation | Dedicated working directory, supported absent-HOME fallback; synthetic catalog only; transient network/debug/achievements settings disabled as in the recipe |

Console records show BIOS and configured ROM loading at about 11:15:19 local time. The final native capture was at 11:20:41 and the emulator then quit with exit 0. These timestamps do not measure time to a usable menu or input latency. No FPS, Naomi heap, texture allocation or continuous memory instrumentation was collected.

## Observations

| Case | Observed result |
| --- | --- |
| Boot/render | Text list, yellow selection arrow/highlight and lower scroll indicator rendered. The one-character first title `A` was selected. |
| Down/Up | One 100 ms Down selected `Amber Circuit`; one 100 ms Up returned to `A`. |
| Scroll to end | From `A`, 25 separate 100 ms Down presses selected the final, 127-character `Zephyr Expedition…` fixture. The list scrolled and its upper indicator appeared. |
| Lower boundary | One additional Down remained on the last title. |
| Release/reverse | A 700 ms Up hold selected the preceding `Willow Orbit`. A later 1500 ms Up hold followed by 26 separate Up presses returned to `A`, confirmed by the final native screenshot. Held-repeat timing and each intermediate selection were not separately captured or accepted. |
| Exit | Application quit normally, process exit 0. The UI observer's final request after quitting reported no running process; this was not a native-menu crash. |

The long title clips at the right edge. This is a recorded text-layout limitation, not a passing full-title readability case. Decide on clipping/ellipsis/details behavior during the later CRT/UI work, using actual cabinet viewing distance; no layout change was made here.

## Evidence and limits

Private local evidence is under ignored `native/out/runtime-tests/emulator-20261113/` and outer `work/flycast-runtime/`. It includes ROM/config/ELF identities, the fixture manifest, native F12 captures and the verbose interpreter log. Task-created native images were also copied into the outer `outputs/` directory for the user. Raw logs, BIOS, persistence and cabinet captures are not committed. The debug console produced about 775 MiB; retain the compressed private copy rather than putting it in a PR.

Not run or accepted: short/long Start, settings/Back/save exchange, real game launch, SRAM, orientation/fallback-font variants, a timed repeat-input test, long soak and target heap/texture telemetry. Stock raw-ROM Flycast lacks the host-message bridge needed for E3. Interpreter speed cannot establish Naomi or JIT performance. Balanced source fixtures and Astra's ownership review do not establish a leak-free runtime.

At this earlier BIOS/rendering checkpoint, the native candidate had **not yet been deployed to Naomi**. A separately approved BIOS-only helper was run, then the original shipped menu was retransferred and its installed host left waiting for selection. Installed CSV/settings/menu hashes matched the preflight backup and no `.sram` file appeared. The CRT was off at that checkpoint, so visual return was then unverified. The later approved Phase A recorded user-confirmed original-menu/controls return; physical EEPROM/SRAM invariance remains unverified. The temporary settings path now aliases the original YAML so ordinary future UI edits persist normally; no additional reset was required.

## Historical next-work note

The following describes the plan at this earlier checkpoint; use the [current handoff](../ai-handoff.md) for the next action after Phase A and the Start-fix check.

Preserve this evidence and finish any useful remaining isolated E2 cases. Then prepare milestone 3's exact candidate launch, backup/rollback, console capture and agreed Naomi case list. Obtain approval for that native comparison; the BIOS capture approval does not authorize it. Keep phone-status acceptance separate. Do not merge the draft native PR as cabinet-accepted or start artwork/video work on the strength of these observations alone.
