# Runtime test result / bug evidence template

Copy this blank template into private evidence storage for each run. Commit only a reviewed/redacted summary if useful. Use synthetic IDs publicly; keep private address/game/settings mappings, raw logs/media, BIOS/ROMs and SRAM outside the checkout or in ignored `native/out/runtime-tests/`. Do not paste credentials or real cabinet settings here.

## Run identity

| Field | Value |
| --- | --- |
| Run ID / operator | |
| Start/end date, time, timezone | |
| Host/Pi/emulator clock offset or unknown | |
| Purpose / roadmap gate | |
| Source branch / full commit / dirty diff identity | |
| PR / source baseline | |
| Base ROM SHA-256 / bytes | |
| Configured runtime ROM SHA-256 / bytes | |
| Synthetic fixture/config SHA-256 / version / redacted differences | |
| Matching ELF SHA-256 / manifest / builder / compiler evidence IDs | |
| Environment: emulator version/backend or Naomi/NetDIMM/JVS revisions | |
| BIOS identity/hash (private if appropriate) / emulator feature limits | |
| Launch source: emulator / OSM / phone / other | |
| Target/game test IDs / prior game test ID / orientation / player count | |
| Debug overlay / verbose flags / other measurement tools | |
| SRAM mode: disabled / synthetic / approved real write scope | |
| Agreed duration/cycles / stop conditions | |

## Hardware scope and recovery (unavailable for an emulator-only run)

| Field | Value |
| --- | --- |
| Existing authorization / concrete approved files and launch cases | |
| Startup/reboot/power coordination, if applicable | |
| Confirmed no active transfer/config edit | |
| Private backup ID / archive SHA-256 / verified contents | |
| Original file hashes / owners / modes evidence ID | |
| Reviewed rollback procedure / restoration verification | |

## Case outcomes

Use `pass`, `fail`, `blocked`, `not run` or `unavailable`. A missing emulator message bridge, log or measurement must include a reason. Selection/settings success does not imply game launch/SRAM/CRT/Single Boot acceptance.

| Case ID / scenario | Exact input sequence and hold durations | Expected | Actual / outcome | Timestamp / repetitions | Evidence IDs / bug ID |
| --- | --- | --- | --- | --- | --- |
| | | | | | |

Include relevant cases from the [runtime plan](../native-runtime-test-plan.md): fixture boot/render/fonts, navigation/repeat/endpoints, short Start, long Start/settings, Back/cancel, both save/exit paths, supported round trips, SRAM association/restore/disabled behavior, chosen game/playability, bounded soak, separately coordinated Single Boot, and separate phone normal/busy/subsequent-game/OSM-to-phone status acceptance.

## Measurements

Define start/end events, units, sample count and method; keep comparison conditions identical. Use `unavailable — reason` instead of guessed values. Separate debugger/overlay runs from normal performance measurements.

| Metric | Original baseline | Candidate | Method / uncertainty / samples / evidence |
| --- | --- | --- | --- |
| Menu payload bytes / upload / unpack time | | | |
| Start event → usable menu | | | |
| Navigation / Back / settings response latency | | | |
| Selection → sender start / playable game confirmation | | | |
| FPS / draw microseconds / frame observations | | | |
| Naomi heap / texture memory / repetition trend, if exposed | | | |
| Pi process RSS, separately labelled if relevant | | | |
| Actual soak duration / cycles | | | |
| CRT mode / readability / overscan / blanking / click count | | | |

## Failure / bug record (repeat per bug)

| Field | Value |
| --- | --- |
| Bug ID / short symptom / impact | |
| First failing case/time / exact last successful action | |
| Minimal reproduction / preconditions / input timings | |
| Expected versus actual | |
| Failures / attempts / earliest known passing build | |
| Screenshot/video IDs and time offsets | |
| Log IDs and matching time interval / job ID / exit status | |
| Raw error code/text / exception / PC/register/backtrace evidence ID | |
| Matching ELF identity used for address interpretation, or unavailable | |
| Settings/SRAM/selection association evidence (private references only) | |
| Diagnostics unavailable / reason / proposed bounded follow-up | |
| Suspected cause versus established evidence | |
| Changed factor / retest result / rollback comparison | |

Capture logs/status before another invocation replaces them. Record capture file checksums in the private evidence index; sanitize copies for publication rather than changing the only raw evidence. No failure injection or automatic launch retry on live hardware.

## Handoff / gate decision

- Gate outcome and cases still unverified:
- Accepted candidate or rollback state; selected original/candidate hashes:
- User-confirmed gameplay observation (or not observed):
- Open bugs, evidence IDs and known diagnostic gaps:
- Exact last action and next bounded action:
- Authorization/coordination needed for that next action, if any:
- Reviewed/redacted findings location and updated [current handoff](../ai-handoff.md):
