# Own-board BIOS capture preparation

This isolated helper built offline and then completed one explicitly authorized own-board capture on 2026-11-13. Two complete volatile 2 MiB reads matched byte for byte; the receiver exited 0 and the private local copy matched the capture hash. Flycast's known BIOS CRC table recognized the image. Firmware bytes, identity and hashes remain private. It does not change the menu, launcher or installed paths. The temporary launch and explicit original-menu return used the reviewed installed flow; a future run still needs its own coordinated window.

The pinned libnaomi `naomi/system.h` defines `BIOS_BASE=0`, `BIOS_SIZE=0x200000` and `UNCACHED_MIRROR=0xA0000000`. The helper reads exactly the 2 MiB uncached BIOS mapping at `0xA0000000`, twice, in fixed 4096-byte chunks. It accepts only the next sequential chunk index across both passes; the host cannot choose an address or length. Messages use dedicated IDs READY/READ/DATA/DONE (`0x2100`–`0x2103`), with little-endian 32-bit indices and exactly 4096 data bytes per reply. Each pass rereads volatile physical bytes; it does not replay a cached first dump. Send failure stops the helper. Unexpected requests are freed and ignored. No retry/resume or arbitrary memory interface is provided.

The capture client only talks to an already launched helper. It contains no upload, reboot, EEPROM/SRAM write or automatic game restore. It validates sequence, size, completion and byte equality for two whole reads before creating an accepted BIOS file. Output must be a fresh directory below ignored `native/out/runtime-tests`; directories are mode 0700 and files 0600, with exclusive creation/no symlink overwrite. Failures leave an empty reserved directory, or partial local evidence if a disk write fails; inspect privately and choose a new directory on retry. A Unix SIGALRM timer enforces the capture deadline even inside the legacy transport loops; run this CLI in its own main process (macOS/Linux). The default deadline is 1800 seconds: two full reads transfer 4 MiB through the existing slow per-register transport. The recorded Pi-local capture took about 27 minutes 18 seconds; other hardware/network paths can be slower, so choose `--timeout` explicitly with adequate headroom. A protocol failure requires restarting the helper in another approved launch window; blindly retrying the client cannot resume its state.

## Local proof

Use the existing builder prepared by `native/build.sh`; this build never downloads or accesses hardware:

```sh
sh native/biosdump/build.sh
python3 -B tests/test_bios_capture.py
git diff --check
```

The Makefile adapts the Unlicense SRAM helper build recipe from hmofet/netboot `6ccbfdd000e705678ee422ebe972c2fccce40693`; the C and host protocol are new, dedicated BIOS-only code. Library/toolchain provenance is recorded in `native/build-env/sources.json`. Build output is ignored at `native/out/biosdump/`: helper ROM, matching debug ELF, symbols, SHA256SUMS and builder identity. Preserve these together before a future capture.

Source inspection of pinned libnaomi startup (`system.c` `_enter`/`_startup`), message/packet initialization and their startup calls found no implicit EEPROM/SRAM writes. The helper avoids video initialization, stdio redirection, EEPROM APIs and SRAM access. Linked ELF inspection finds no `eeprom_write`, `maple_request_eeprom_write` or SRAM symbols. This is a helper-code claim, not a guarantee that Naomi BIOS booting a different ROM leaves game/system settings unchanged: BIOS boot behavior and physical EEPROM/SRAM invariance have not been verified by this capture. Startup still initializes normal libnaomi hardware services and message scratch registers; read-only refers specifically to BIOS/EEPROM/battery SRAM, not all machine registers.

Six host test cases cover two full sequential passes, wrong type/truncation/out-of-range sequence, different second read, readiness/completion and private/exclusive output. Those tests use synthetic bytes; separate authorized hardware evidence is recorded below. A matching hash establishes repeatability, not identification of a known-good BIOS or emulator compatibility.

## Reviewable capture and rollback plan

A no-network dry run, safe to execute locally:

```sh
python3 -B native/biosdump/capture.py example.invalid \
  --output-dir native/out/runtime-tests/bios-own
```

For a future approved window: first preserve the currently selected game/menu and installed configuration using the existing reviewed launch procedure in `docs/loading-status.md`; verify idle transfers and the exact target. Hash the helper and matching debug ELF. Launch only `native/out/biosdump/biosdump.bin` through the existing reviewed standalone sender flow (its normal CRC bypass and final reboot), substituting a separately verified target. This document intentionally supplies no automated upload/reset command; the capture CLI cannot perform one. Keep target details in private session notes. Starting the helper replaces the running game until an explicit subsequent launch. No launcher/config installation is needed.

Once the separately approved helper launch has occurred, create the ignored parent locally (`mkdir -p native/out/runtime-tests`), then run the same command with the verified target instead of `example.invalid` and add `--connect`. This explicitly enables message traffic only. Run it once, from a host with the existing `dm_netboot` Python dependencies available. Save returned SHA-256 and both-complete-read result privately. Do not commit BIOS bytes, addresses, private logs or cabinet settings.

Rollback is an explicit ordinary launch of the previously recorded game/menu through the existing reviewed launch flow, after capture has exited and no transfer is active. Do not alter defaults, restore EEPROM/SRAM or automate a second game launch. Confirm cabinet return with the user; successful helper build/capture is not rollback or gameplay acceptance. Review actual command/target and backup evidence before any live action.

Current local build (2026-11-13): ROM 106,388 bytes, SHA-256 `c81c1ee20dcdbdb02a8e1eac850265be010585f1abf43829164c1bf88622c810`; debug ELF SHA-256 `744f25639599492cee4258fe1691fda3784aea8abaf2f5894e4ebf9c4d143aa1`; existing builder image `sha256:07752cb87e3705adf329c281a0b94079275cec6fef124701880913b2b7799967`. The subsequent authorized live result is recorded below.

The existing libnaomi message reassembly trusts packet fragment offsets before application validation. This helper assumes a trusted, unmodified local host/NetDIMM transport; it does not establish memory safety against hostile malformed transport fragments. Its fixed read bounds apply to valid application requests, not arbitrary wire corruption inside upstream message reassembly.

Live outcome, 2026-11-13: the user switched Naomi on and explicitly approved the temporary helper launch/capture/return-to-menu run. Preflight found Checking network, no active host loader/menu processes, and target SRAM saving already false. Existing `/opt/wipi64-venv/bin/python` supplied dependencies with its PATH inherited by subprocesses. The helper transferred and reset once. Capture completed exit 0 in approximately 27 minutes 18 seconds; two whole volatile 2 MiB reads were byte-identical, and the copied private BIOS matched the capture hash and a known Flycast BIOS CRC entry. Capture prints one progress line per 64 accepted chunks per pass.

The root agent then retransferred the original shipped menu and reset once through installed `netdimm_menu`, using an exact settings clone with SRAM already false. Host evidence recorded transfer length `000d8b38` followed by waiting for ROM selection. Original installed CSV/settings/menu binary hashes remained unchanged and the SRAM directory still contained README only. The native menu candidate was not deployed. The CRT was off, so visual menu return and physical EEPROM/SRAM invariance remain unproven; unchanged host files do not establish either. Private backups and raw evidence are retained outside tracked source. No BIOS bytes/identity/hash or private target details are committed.

After return, the exact cloned settings file was retained as evidence and its temporary path atomically aliased to the unchanged original installed YAML. Normal future menu settings edits therefore persist to the usual file without another transfer/reset. The installed YAML itself was not changed by that alias operation.
