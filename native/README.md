# Native text-menu baseline

This is an experimental, rebuildable source baseline for the Naomi on-screen menu. It is the prerequisite for adding artwork, not the artwork implementation. Nothing here changes the runtime launcher or replaces `sbin/piforce/dm_netboot/homebrew/netbootmenu/netbootmenu.bin` (including its dark/light variants).

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

The focused tests compile actual C configuration/SRAM code with fake hardware memory and message I/O. They use the actual host serializer expression, check both SRAM flag values, snapshot bytes, successful restore, malformed/disabled restores with guard bytes, unrelated message ownership and sender error propagation. These tests do not exercise real battery SRAM, JVS, video or NetDIMM communications.

## Before any hardware comparison

Keep this baseline as a draft until an isolated runtime comparison is planned. Verify the installed host and menu files, preserve all existing menu binaries, settings and SRAM saves, and obtain approval for a concrete backed-up test. Do not overwrite a working binary just because compilation succeeded. Rollback means restoring the original selected menu binary and associated host files together if those were changed; this branch does not change those host files.

Pending checks: actual video/input and settings screens, SRAM backup association with the previous game, restoration before the next game, game selection/upload, menu startup timing, orientation and Single Boot. Coordinate startup tests with the user and retain the OSM/phone transfer restriction. The new phone status screen also still needs its separate hardware acceptance.

Once baseline behavior is established, add artwork as a separate five-game proof with bounded payload parsing, missing-image fallback and measured memory/startup cost. See the [illustrated-menu investigation](../docs/illustrated-osm-investigation.md).

The user also requests a post-baseline feasibility check for a selected-game view with video and information below it, inspired by the phone interface. Follow the [CRT experience and performance checks](../docs/illustrated-osm-investigation.md#post-baseline-check-game-details-video-and-crt-experience) before choosing any playback approach. This baseline includes no movie decoder/player. Preserve responsive launch/Back controls and a still-image/details fallback; do not promise video without added delay until it is measured on Naomi.
