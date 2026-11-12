# Native text-menu baseline

This is an experimental, rebuildable source baseline for the Naomi on-screen menu. It is the prerequisite for adding artwork, not the artwork implementation. Nothing here changes the runtime launcher or replaces `sbin/piforce/dm_netboot/homebrew/netbootmenu/netbootmenu.bin` (including its dark/light variants).

Current source/artifact identity and acceptance state live in [the AI handoff](../docs/ai-handoff.md). Follow [the ordered gates](../docs/roadmap.md), [emulator/Naomi diagnostic plan](../docs/native-runtime-test-plan.md) and [result template](../docs/templates/runtime-test-result.md) when resuming runtime work. The bare build ROM needs the separately hashed synthetic configuration section described below before isolated emulator use. No emulator host-message bridge is supplied.

## Source and changes

The renderer and original assets come from [hmofet/netboot at 6ccbfdd](https://github.com/hmofet/netboot/tree/6ccbfdd000e705678ee422ebe972c2fccce40693/homebrew/netbootmenu). `netbootmenu/upstream.json` records the original file hashes. Preserve the Unlicense and bundled font notices in `netbootmenu/LICENSE` and `netbootmenu/FONT-LICENSE.txt`.

The recovered source predates WiPi's SRAM additions. This baseline adds:

- A fixed-width, packed 64-byte configuration matching WiPi's current Python serializer: SRAM flag at byte 32, calibration at 36, font fields at 48/52 and player count at 56. Compile-time checks also enforce 136-byte game records.
- A startup snapshot of the full 32 KiB battery SRAM when backup is enabled, sent as `0x2003` for the host to save under the previously played game. This occurs once per menu startup; toggling backup on takes effect for snapshots on the next startup.
- `0x2004` restore handling shared by all eight screen receive paths, including the unpack/loading screens. It accepts exactly 32 KiB only when enabled, uses the uncached SRAM mirror, frees consumed messages and preserves unrelated messages for their original screen. Rejected restores and snapshot send failures are logged to the host.
- An SRAM enable/disable setting carried through both save-and-exit control paths. Configuration saves still use the host's 64-byte protocol.

The original renderer's joystick, short-Start selection, long-Start settings and text-list rendering remain in place. They have compiled, but their runtime behavior has not been verified in an emulator or on the cabinet. This is not a byte-for-byte reproduction of the installed binary.

## Build and local proof

Requires Docker with `linux/amd64` support and host Python 3. Network access is needed to obtain the pinned builder, APK/Python build dependencies and source archives. All actual menu compilation then runs with networking disabled, a read-only source mount and temporary writable build storage. No SSH, NetDIMM sender or deployment command is used.

```sh
sh native/build.sh
python3 -B tests/test_native_menu.py
git diff --check
```

The host tests require a C compiler. Alternatively, after building the image:

```sh
docker run --rm --platform linux/amd64 --network none \
  -v "$PWD:/repo:ro" wipi-native-builder:baseline \
  python3 -B /repo/tests/test_native_menu.py
```

`build-env/Dockerfile` pins the compiler distribution by digest and libnaomi by commit/archive checksum. Source dependencies have checksums in `build-env/sources.json`, and Python build requirements are version-pinned. Third-party library builds run serially because their upstream recursive make rules do not preserve parallel jobserver descriptors. Build dates are fixed to the baseline version, 2026-11-13.

Artifacts are written to ignored `native/out/`: the menu ROM, debug ELF, SHA-256 checksum, source manifest, compiler/ELF details, Python package versions and local builder image ID. `check-rom.py` validates the ROM header, serial, date, entry points, file section bounds and separation from the host configuration area at `0x0D000000`.

The focused tests compile actual C configuration/SRAM code with fake hardware memory and message I/O. They use the actual host serializer expression and check both SRAM flag values. The SRAM fixture runs 1,000 cycles with 7,000 successful allocations and 7,000 matching frees. Each cycle covers snapshot bytes, allocation/send failure, successful restore, malformed/disabled restores with guard bytes and unrelated message ownership passed to the caller.

The settings fixture compiles the exact parser and settings-load caller regions from `screens.c` with UI and message stubs; it does not compile or exercise the rest of the renderer. A valid settings packet includes patches, two system settings and two game settings, each with selectable values and conditional read-only dependency arrays. All 155 truncated prefixes must return failure with balanced allocations, including a missing game-settings count after complete system settings and failure in a later setting. Caller checks cover parse failure, a different selected game and successful ownership until explicit release. A valid response after the no-ACK timeout must retain settings ownership and enter the settings screen; an absent response must still time out. The Python status suite separately retains real opened lock files to verify immediate closure on initialization failures in `flock`, progress reads/stat, job identity, process identity, timestamps and saving, as well as duplicate-lock rejection. A later launch must still acquire the lock.

For a Linux compiler with sanitizer runtimes installed, instrument both native fixtures with:

```sh
NATIVE_TEST_CFLAGS='-g -O1 -fno-omit-frame-pointer -fsanitize=address,undefined' \
  ASAN_OPTIONS='detect_leaks=1:halt_on_error=1' \
  LSAN_OPTIONS='exitcode=23' UBSAN_OPTIONS='halt_on_error=1:print_stacktrace=1' \
  python3 -B tests/test_native_menu.py
```

Allocation counters measure only the exercised ownership paths. The settings tests do not cover allocation exhaustion or arbitrary malformed count fields. Host fixtures and sanitizers do not exercise real battery SRAM, JVS, video, fonts, NetDIMM communications or long-running menu behavior. Passing these checks does not exclude all hardware/runtime leaks; emulator and cabinet acceptance remain pending.

## Offline emulator fixture

With the existing builder image and pinned base ROM available, run these commands from the repository root. They use no network, sender, cabinet catalog or live host entry point. Only the ignored build-output mount is writable during generation.

```sh
docker run --rm --platform linux/amd64 --network none --read-only \
  -v "$PWD:/repo:ro" wipi-native-builder:baseline \
  python3 -B /repo/tests/test_emulator_fixture.py
docker run --rm --platform linux/amd64 --network none --read-only \
  -v "$PWD:/repo:ro" -v "$PWD/native/out:/repo/native/out" \
  wipi-native-builder:baseline python3 -B /repo/native/create-emulator-fixture.py
```

The generator requires the exact reviewed base identity in the handoff and rejects a changed, truncated or already configured ROM. A future baseline requires an explicit reviewed pin update. It uses the installed `naomi.add_or_update_section` helper to append one main-executable section at `0x0D000000`, then verifies the old section descriptors, executable bytes, entry points and appended bounds. The original base remains unchanged.

Outputs under ignored `native/out/emulator/` are `configured-menu.bin`, `synthetic-config.bin`, `fixture-manifest.json` and `SHA256SUMS`. The 3,600-byte synthetic section contains a 64-byte configuration and 26 invented 136-byte game records. IDs equal zero-based list indices; initial selection is zero. The first title is one character, the last is 127 ASCII characters plus its terminator, and the list exceeds the 20 visible rows at 640×480. Digital controls, export region, two players, centered/full-range calibration, muted sound and disabled SRAM are fixed. Debug overlay, optional fallback font and filename mode are off. The tests compare configuration bytes with the actual host serializer expression, check record boundaries/IDs/names, and reject malformed payloads and wrong base identities. All four tests passed on 2026-11-13.

Keep these outputs together with the matching base manifest, ELF and builder/package records in `native/out/` when preserving evidence. Fixture generation proves layout and identity only. No game ROM or BIOS is included, and a synthetic title is not a launchable game. Use isolated emulator persistence: existing native startup still writes emulated EEPROM game settings even with SRAM disabled. Browsing can be tested independently once emulator readiness is resolved, but Start/settings host round trips need a verified isolated message bridge. Source inspection shows that Flycast v2.7's stock raw-BIN cartridge route lacks that bridge; no adapter has been implemented. See [runtime readiness](../docs/native-runtime-test-plan.md#stage-e-isolated-emulator-preparation-and-baseline) for the current BIOS blocker; no render/navigation run has occurred.

## Before any hardware comparison

Keep this baseline as a draft until an isolated runtime comparison is planned. Verify the installed host and menu files, preserve all existing menu binaries, settings and SRAM saves, and obtain approval for a concrete backed-up test. Do not overwrite a working binary just because compilation succeeded. Rollback means restoring the original selected menu binary and associated host files together if those were changed; the native menu work does not change the sender/menu-host scripts or installed launcher selection. PR #2 also contains an `upload_status.py` initialization-failure cleanup fix beyond the merged PR #1 baseline; include it in any separately scoped phone deployment review, not an unrecorded native comparison.

Use the [diagnostic readiness gate and capture plan](../docs/native-runtime-test-plan.md#stage-n-approved-backed-up-naomi-comparison) before an approved comparison. Pending checks: actual video/input and settings screens, SRAM backup association with the previous game, restoration before the next game, game selection/upload, menu startup timing, orientation and Single Boot. Coordinate startup tests with the user and retain the OSM/phone transfer restriction. The new phone status screen also still needs its separate hardware acceptance.

Once baseline behavior is established, add artwork as a separate five-game proof with bounded payload parsing, missing-image fallback and measured memory/startup cost. See the [illustrated-menu investigation](../docs/illustrated-osm-investigation.md).

The user also requests a post-baseline feasibility check for a selected-game view with video and information below it, inspired by the phone interface. Follow the [CRT experience and performance checks](../docs/illustrated-osm-investigation.md#post-baseline-check-game-details-video-and-crt-experience) before choosing any playback approach. This baseline includes no movie decoder/player. Preserve responsive launch/Back controls and a still-image/details fallback; do not promise video without added delay until it is measured on Naomi.
