# Isolated Flycast v2.7 local build

This recipe preserves the 2026-11-13 macOS arm64 preparation. Build success and `--help` success are separate from ROM execution. No emulator rendering/navigation or NetDIMM bridge is established by either check. Keep BIOS, ROMs, configuration and runtime evidence private.

## Source and workspace tools

Use an outer working directory, outside this repository. Source is official [Flycast v2.7](https://github.com/flyinghead/flycast/tree/5aa091fde632fb332c8d8c34e280d62dc951954c), commit `5aa091fde632fb332c8d8c34e280d62dc951954c`. Submodule identities are recorded in [the source inventory](../native/emulator/flycast-v2.7-submodules.txt). The required tested subset below was initialized recursively and verified. Leading `-` entries identify unused, uninitialized modules in that inventory; they are expected, not missing build dependencies. Do not require every optional submodule for this host-SDL build. This is source preparation, not a globally installed application.

```sh
git clone --branch v2.7 https://github.com/flyinghead/flycast.git flycast-source
git -C flycast-source checkout 5aa091fde632fb332c8d8c34e280d62dc951954c
git -C flycast-source submodule update --init --recursive \
  core/deps/libchdr core/deps/libjuice core/deps/websocketpp \
  core/deps/tinygettext core/deps/freetype core/deps/rcheevos \
  core/deps/asio core/deps/Syphon core/deps/DreamPicoPort-API
python3 -m venv flycast-build-tools
flycast-build-tools/bin/python -m pip install cmake==4.4.4 ninja==1.13.2
```

Existing host dependencies were used, including SDL2, libzip, libpng and libomp from Homebrew, plus Xcode and its macOS SDK. No new system package installation is implied by this recipe. Exact transitive host dependency versions are not fully pinned; the binary is local evidence, not a reproducible portable distribution. Apple clang was `21.0.0 (clang-2100.4.1.1)`. Link warnings report some host dependencies built for macOS 27.0 despite the app deployment target of 13.0.

Apply [the build-only patch](../native/emulator/flycast-v2.7-macos-build.patch) in the source checkout. Its SHA-256 is `68c1b76288d55cbe4f83b0a587b8b330e8417c875c12e2b13c53be74840fc75f`. It disables inherited C++ PCH only for the macOS Flycast target, keeping Syphon's required prefix header, and copies MoltenVK only when Vulkan is enabled. No emulator behavior or protocol adapter changes are included. The stored patch uses zero context so patch-format context whitespace does not create false whitespace-check failures. Applying it to the pinned original was checked to reconstruct the exact already-built CMake file. Pass the absolute patch path from your checkout:

```sh
git -C flycast-source apply --unidiff-zero /absolute/path/to/wipi-fork/native/emulator/flycast-v2.7-macos-build.patch
```

## Configure and build

From that outer working directory, with the workspace tool directory on PATH for Ninja discovery:

```sh
export PATH="$PWD/flycast-build-tools/bin:$PATH"
SDK_PATH=$(xcrun --sdk macosx --show-sdk-path)
flycast-build-tools/bin/cmake -S flycast-source -B flycast-build -G Ninja \
  -DCMAKE_POLICY_VERSION_MINIMUM=3.5 -DCMAKE_PREFIX_PATH=/opt/homebrew \
  -DCMAKE_BUILD_TYPE=RelWithDebInfo -DCMAKE_OSX_ARCHITECTURES=arm64 \
  -DCMAKE_OSX_DEPLOYMENT_TARGET=13.0 -DCMAKE_DISABLE_PRECOMPILE_HEADERS=OFF \
  -DUSE_HOST_SDL=ON -DUSE_HOST_LIBZIP=ON -DUSE_OPENGL=ON -DUSE_VULKAN=OFF \
  -DUSE_BREAKPAD=OFF -DUSE_LUA=OFF -DENABLE_LOG=ON \
  -DENABLE_GDB_SERVER=ON -DZLIB_LIBRARY="$SDK_PATH/usr/lib/libz.tbd"
flycast-build-tools/bin/cmake --build flycast-build --parallel 8
```

The policy minimum flag is required for CMake 4 with older bundled dependency CMake files. Host SDL is used, so its optional source submodule is not initialized. The checked build exited 0. `flycast-build/Flycast.app/Contents/MacOS/Flycast` was 14,520,760 bytes with SHA-256 `e0cc552a836a70ea8fce5d16b145a8dcd301351b1a13b00eb05a3c8234b064d0`. Keep local CMakeCache and logs with the executable; repeat the identity checks after changes.

## Isolated CLI and future ROM run

On macOS, `shell/apple/emulator-osx/emulator-osx/osx-main.mm` reads HOME before parsing CLI flags. With HOME absent it explicitly uses `./` for configuration/data; ordinary `--help` under the user's environment can create user preferences before parsing. Use its supported fallback from a dedicated private directory:

```sh
mkdir -p flycast-runtime
chmod 700 flycast-runtime
cd flycast-runtime
env -u HOME ../flycast-build/Flycast.app/Contents/MacOS/Flycast --help
```

The root agent verified this exact isolated CLI path exited 0. This does not initialize or test a ROM. Do not copy a real cabinet catalog/settings into a synthetic test. A future approved E2 run uses the existing synthetic configured menu, lawful own-board BIOS in the isolated data lookup path, and the same absent-HOME working directory. A lawful own-board BIOS was subsequently captured privately, but emulator memory setup failed before loading it; the interpreter-only fallback later supplied the [bounded rendering/navigation evidence](results/2026-11-13-native-emulator.md). E3 host round trips remain unsupported on stock raw ROM.

Network/debug settings can be disabled using transient CLI settings (not saved to emu.cfg):

```sh
env -u HOME ../flycast-build/Flycast.app/Contents/MacOS/Flycast \
  -config 'network:Enable=no,network:EnableUPnP=no,network:GGPO=no,network:NetworkOutput=no,network:BattleCable=no,network:EmulateBBA=no,network:NaomiSatellite=no,network:DCNet=no' \
  -config 'config:Debug.GDBEnabled=no,config:Debug.GDBWaitForConnection=no' \
  -config 'achievements:Enabled=no' /absolute/path/to/synthetic-configured-menu.bin
```

This command was subsequently attempted with the private synthetic fixture, once with default JIT and once with runtime Dynarec.Enabled=no; both exited 133 before BIOS/ROM loading at the SH4 memory-layout assertion. Neither attempt executed the native candidate. Source defaults already disable network play, GGPO, output server and GDB, but UPnP defaults true; explicit overrides avoid inheriting an accidental network/debug configuration. They are application settings, not an operating-system network sandbox. `NetworkOutput` would bind TCP 8000 when enabled. No guarantee of zero sockets is inferred without observing a run. Avoid adding controller accessories or peripherals for the first test; fresh config registers the SDL keyboard on port 0 and controller auto-discovery can see connected devices. Do not disable SDL joystick initialization with an undocumented emulator flag.

Default keyboard mapping (`core/input/keyboard_device.h`, SDL keyboard scan codes) is arrows for direction, Return for Start, X/C/S/D for A/B/X/Y, Q for coin, Tab for emulator menu, Space for fast-forward, F12 for screenshot. `core/hw/maple/maple_jvs.cpp` maps DC Start/up/down directly to Naomi Start/up/down. Use the GUI Controls page to confirm keyboard assigned to player 1 before interpreting failed input; per-device/per-game mappings can override defaults. The native menu polls JVS; focus, layout, port and actual emulated JVS behavior remain runtime checks. Start can enter unsupported host-dependent paths; preserve a baseline rendering/navigation capture before trying it.

## Supported interpreter-only fallback after startup failure

Both local GUI attempts failed before BIOS/ROM load at the recompiler's VMEM layout assertion (`core/hw/sh4/dyna/driver.cpp:349`). `Emulator::init()` initializes the compiled recompiler before consulting runtime `Dynarec.Enabled`; turning that setting off cannot avoid this startup failure. The recorded RAM/base addresses violate the expected relation. The underlying mapping anomaly remains undiagnosed; no assertion or protection was removed.

A bounded fallback uses the existing `TARGET_NO_REC` build feature from `core/build.h`, disabling SH4/AICA/DSP dynarecs. Build into a **separate** directory using the complete configure command above, changing `-B` to `flycast-build-interpreter` and adding:

```sh
-DCMAKE_CXX_FLAGS=-DTARGET_NO_REC -DCMAKE_C_FLAGS=-DTARGET_NO_REC -DENABLE_GDB_SERVER=OFF
```

Use `flycast-build-tools/bin/cmake --build flycast-build-interpreter --parallel 8`. GDB must be OFF for this combination: the first fallback attempt with it ON compiled but failed linking `GetRegPtr`, which GDB references from dynarec-only code. With GDB OFF the fallback build exited 0; `nm -C` showed `Sh4Interpreter::Init()` and no `Sh4Recompiler::Init()`. Interpreter code has its existing default underclock behavior, so future speed observations are not JIT performance measurements.

Fallback executable: `flycast-build-interpreter/Flycast.app/Contents/MacOS/Flycast`, 14,031,720 bytes, SHA-256 `2b8dcf7a8670046d3b98b56f647e52af3da8445eddf7a05545b00713c4f1fcf6`. The local configure/build logs are `work/flycast-interpreter-configure.log` and `work/flycast-interpreter-build.log`. A subsequent isolated run loaded the private BIOS and synthetic ROM, rendered and navigated the list, and quit with exit 0; see the [dated result](results/2026-11-13-native-emulator.md). The JIT mapping anomaly remains unresolved, so this is not JIT/performance acceptance. No VMEM bypass, source bridge or speculative emulator fix was added.

For the observed successful run, use the same isolated launch command above with `../flycast-build-interpreter/Flycast.app/Contents/MacOS/Flycast` and `-config config:Dreamcast.Region=0`. Start/settings were not exercised because the stock raw-ROM bridge is absent. The debug build emits a large register trace (about 775 MiB in the bounded session); preserve/compress it privately and close the emulator after the case list rather than leaving it running. Native F12 screenshots use the macOS Pictures directory even with HOME absent; copy the task-created synthetic captures to the private result bundle.
