# Game artwork in the arcade on-screen menu

## Request and conclusion

Investigate an interactive default arcade menu showing game artwork and titles, using the phone game list as the visual reference. This refers to the menu displayed by Naomi on the CRT, navigated with the cabinet joystick/buttons.

An illustrated native menu is technically plausible: Naomi has image-rendering and JVS-input support, and libnaomi provides a sprite example combining both. It is not an existing WiPi artwork setting or a CSS change. Our current menu payload has no image data/reference, and this checkout only contains compiled menu binaries. Implementation needs rebuildable menu source and a matching host-side artwork payload. No product code or Pi settings were changed; no prototype has been compiled or tested in an emulator or on the cabinet.

## Evidence from this fork

- `sbin/piforce/singleboot.py` starts `menulauncher.py` for the menu default. In default mode, that script invokes `dm_netboot/netdimm_menu`, optionally with persistent replay behavior.
- `dm_netboot/scripts/netdimm_menu.py` reads the catalog, filters installed/enabled entries and orientation, sorts titles, then appends configuration to a Naomi menu ROM and sends it to the NetDIMM. The menu program runs on Naomi, separately from the Pi's web interface.
- Each current game record has a 128-byte name, four-byte serial and four-byte index. Configuration also supports settings and an optional fallback font, but no artwork field. The script handles menu selection/settings messages and sends the chosen game. Replacing this flow with a browser would require a different video/input architecture.
- `var/www/html/gamelist.php` obtains artwork filenames from `romsinfo.csv` column index 2 and titles from index 4. The repository's `var/www/html/images` is a symlink to `/boot/config/images`. This provides a candidate mapping to reuse, not proof that every image is present or suitable for the CRT. Do not commit cabinet assets automatically.
- `homebrew/netbootmenu/` contains `netbootmenu.bin`, `.bin.dark` and `.bin.light`; the menu renderer's source/build rules are absent from this checkout. Switching those binaries does not supply a game-artwork protocol.
- The public DragonMinded/netboot source URL returned HTTP 404 through both the GitHub connector and CLI during this investigation. Search results still reference it, so recheck availability rather than assuming permanent removal. An older Fredobedo/netboot snapshot did not contain the required menu renderer either. Recovering matching source and its build requirements is the next concrete prerequisite.

## Platform support and limits

At inspected [libnaomi revision c840eb8](https://github.com/DragonMinded/libnaomi/tree/c840eb85384725182392ee3361706e80ae4ca4c0):

- The [sprite example](https://github.com/DragonMinded/libnaomi/blob/c840eb85384725182392ee3361706e80ae4ca4c0/examples/spritetest/main.c) initializes video, loads image textures and changes pages using JVS joystick/start input.
- Its [Makefile](https://github.com/DragonMinded/libnaomi/blob/c840eb85384725182392ee3361706e80ae4ca4c0/examples/spritetest/Makefile) converts PNG assets to RGBA4444 for the Naomi build. Phone images cannot simply be linked as web URLs inside the existing payload.
- The [toolchain instructions](https://github.com/DragonMinded/libnaomi/blob/c840eb85384725182392ee3361706e80ae4ca4c0/README.md) describe the SH-4 build environment, graphics, input and NetDIMM host communication.

These establish platform capability, not compatibility with the installed menu binary/protocol. Actual resolution/layout, available memory, artwork conversion, menu transfer time, rendering performance and physical JVS behavior need verification. Images increase the payload; load only visible images as textures rather than assuming the full catalog fits in video memory.

## Recommended first design

Start with a readable game list plus one large artwork/title panel for the highlighted game, a clear selection highlight and button hints. Up/down changes selection, the preview follows it, and the cabinet's confirm control launches the chosen game. Missing artwork falls back to the title. This aims for the phone's game-and-image presentation while fitting a landscape CRT and joystick navigation.

A small card grid is an alternative for a later mock-up; the phone's long portrait layout may not be readable unchanged. Filters, animation and video previews are separate proposals. Keep a text-menu fallback and preserve enabled-game/orientation selection, custom entries, settings/SRAM behavior, Single Boot and the existing transfer lifecycle. Browsing must not reboot Naomi or start a game upload on every selection change.

## Staged investigation and acceptance

1. Obtain the renderer source with its license and build instructions. Identify the version corresponding to the shipped menu and reproduce a baseline build before modifying it. If matching source cannot be obtained, explicitly scope a replacement menu; do not treat binary patching or a toolchain upgrade as approved.
2. Make a CRT-proportioned static layout preview using representative logos and long titles. Compare the list/preview with a small grid for readability. Preserve video wiring; no Pi kiosk is needed for this route.
3. Build an isolated five-game proof with artwork embedded in the menu payload, prepared on the host. Preserve sender behavior and game IDs. Include bounds/version checks for new data and retain the original menu for rollback. Test missing/invalid artwork, memory limits and selection-to-game mapping.
4. Check rendering and controls in a suitable Naomi emulator where supported, then prepare a backed-up cabinet comparison for approval. Emulator success does not establish physical JVS, CRT or NetDIMM behavior.
5. On approved hardware testing, check startup time, browsing responsiveness, title readability, correct game launch, settings and Single Boot/OSM behavior. Expand the catalog only after the proof passes. Coordinate this after acceptance of the current loading-status enhancement.

An illustrated menu does not resolve the separate [CRT signal-loss clicking investigation](crt-sync-follow-up.md); the game-start reset remains. It also does not coordinate independent OSM and phone transfers. Preserve that restriction until coordination is separately designed.
