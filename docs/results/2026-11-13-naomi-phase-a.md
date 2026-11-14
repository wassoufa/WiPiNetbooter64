# Naomi Phase A: bounded text-menu comparison, 2026-11-13

The user explicitly approved the reviewed two-reset comparison, including startup EEPROM effects and incomplete physical rollback. Original and candidate menus passed the agreed directional navigation and 60-second idle observations. The original shipped menu was then returned, and the user confirmed its menu and controls work. This is bounded rendering/directional evidence, not full native-menu acceptance. PR #2 remains a draft.

## Identity, preparation and scope

The candidate was selected temporarily with the existing installed `netdimm_menu --exe` flow, using a verified raw base ROM and a regular private settings clone with SRAM OFF. No installed host code, menu binary, defaults or game patches were replaced. The 22 source-manifest hashes, base ROM and exact clone were verified. A fresh 34-member private backup passed disposable offline recovery rehearsal of file bytes/hashes, numeric ownership and modes; that rehearsal was not an installed or physical EEPROM restoration.

| Item | Verified identity/evidence |
| --- | --- |
| Candidate base | 1,461,884 bytes; SHA-256 `3ec9d4faede2fa57a1a3cf1993d5eef7e2aefcb00d7ce800432d93a819fd62a2`; matching ELF SHA-256 `1140b82d970918a2bcfe6d2d9b6078e35e9c7c4d20e4801731579f4f90dc83d7`; build records retained. |
| Host-configured candidate | 1,485,340 bytes; SHA-256 `7659261730609dfa44abfcd420f02a070e084669ff3b9ef4472f8a088fc67e0e`; 172 records. Configuration/catalog bytes match the original payload, and base candidate CPU bytes were preserved. |
| Original return | 887,608 bytes; configured payload matches the pre-BIOS original byte for byte. |
| Host-side timing | Pre-launch timestamp 01:11:32 UTC; candidate upload completed 01:11:40.584 UTC; host waiting for selection 01:11:40.791 UTC. Original-return pre-launch timestamp 01:16:46 UTC, host waiting 01:16:54.889 UTC. Pre-launch timestamps are recorded command-window markers, not exact sender starts. Melbourne local time is UTC+11: approximately 12:11:40 candidate host wait and 12:16:54 return wait on November 13. These are host events, not user-measured usable-menu or gameplay times. |

Identity evidence is the verified staged/configured file, upload record and user observations. No target ROM readback occurred. Cabinet titles/IDs/addresses, settings, screenshots and raw logs remain private.

The comparison performed exactly two AI upload/reset cycles: candidate, then original-menu return. It included no Start, Test/Service, settings/save, game launch, SRAM enable/restore, optional debug, Pi/cabinet power or startup/default test. The user had manually restarted Naomi earlier to recover original controls; that is separate from these two comparison transfers.

## Pre-candidate original-control recovery

Before the comparison, the original menu was visible with animation moving, but the user reported both players' Up/Down inactive and no scroll sounds. The pre-BIOS and restored original configured payloads were byte-identical, ruling out a serialized payload mismatch between those checkpoints. After the user's usual manual Naomi restart, the original cursor moved again; the nonpersistent Pi menu host exited on communication loss. This recovered original baseline was used for the comparison. Root cause remains unproven; a JVS/peripheral state explanation is a hypothesis, not a diagnosis.

## Observed cases

| Case | Original baseline | Candidate |
| --- | --- | --- |
| Ten Up and ten Down taps | User reported normal. | User reported normal. |
| Up and Down held two seconds each | User reported normal. | User reported normal. |
| First/last endpoints | User reported normal. | User reported normal. |
| 60-second idle | User reported stable. | User reported stable. |
| Visible menu | Original text list visible. | Familiar responsive text list visible, expected for this baseline. |
| Explicit original-menu return | Not applicable. | User confirmed original menu and controls work after return. |

An initial incorrect display-choice reply was corrected by the user with a photo showing the familiar text list. It was not a blank/error-screen failure. Similar appearance is expected: this is the text baseline, not an artwork implementation. Appearance alone does not establish binary identity.

No unexpected SRAM file or host log error was observed. No detailed CRT readability/overscan budget, frame timing, heap/texture telemetry or sustained soak was established. The 60-second idle observation must not be described as memory-soak acceptance. Original upload/startup timing was unavailable because the baseline was already loaded; user-confirmed usable-menu timing was not measured.

## Return and remaining limits

The primary agent preserved candidate logs/payload/clone, verified the candidate host identity and stopped it with TERM using pidfd, confirming exit before return. The installed original host was launched without candidate `--exe`, using the real original YAML. It uploaded the byte-matching original payload, reached waiting for selection, and remains active. Future ordinary menu edits use their normal real settings path. The native candidate is not selected persistently.

All 24 installed non-log regular files from the preflight archive matched current SHA-256, numeric UID/GID and modes, including original menu variants, host/wrappers/transports, CSV/catalog, settings/mode files and last-game marker. Logs changed as expected and were excluded from that 24-file comparison; the preflight archive had 34 total members including directories/logs. The candidate clone was unchanged and SRAM directory remained README only. Private live-session evidence was preserved in a 2.7 MiB archive. Host-file invariance and successful menu return do not prove physical EEPROM/SRAM invariance. Candidate startup explicitly clears/writes game EEPROM even with SRAM OFF; no physical EEPROM snapshot/restore was established.

Start/settings/ACK/save/gameplay, SRAM association/restore, Single Boot, optional integrations, orientation/fallback-font variants, resource exhaustion and target heap/texture soak remain unaccepted. The source-level Start release-before-hold-transition hazard is unchanged: future settings testing must be separately gated and must not use a blind “hold one second, then release” instruction. See the [prepared plan](../native-naomi-comparison-plan.md).

Post-run metadata and private-evidence preservation are complete. Next bounded work is review of this limited result and a separately scoped proposal for remaining tests, not another launch. Later protocol/settings/game/SRAM tests require separately reviewed scope and authorization. No artwork/video or phone-status deployment follows from this result.
