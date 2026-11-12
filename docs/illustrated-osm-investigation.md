# Game artwork in the arcade on-screen menu

## Request and conclusion

Investigate an interactive default arcade menu showing game artwork and titles, using the phone game list as the visual reference. This refers to the menu displayed by Naomi on the CRT, navigated with the cabinet joystick/buttons.

An illustrated native menu is technically plausible: Naomi has image-rendering and JVS-input support, and libnaomi provides a sprite example combining both. It is not an existing WiPi artwork setting or a CSS change. The current runtime menu payload has no image data/reference. Renderer source has been recovered and adapted into an [experimental native text baseline](../native/README.md), with WiPi's configuration layout, guarded SRAM exchange and a successful local cross-build. The baseline has no game artwork and has not replaced the shipped binaries or been tested in an emulator/on the cabinet. No Pi changes were made.

An [offline interactive layout preview](previews/illustrated-osm.html) demonstrates five entries, four existing catalog logos and missing-artwork fallback. Open the downloaded HTML file in a browser; arrows move selection and Enter previews confirmation without launching anything. Browser checks verified image/title changes, keyboard navigation, confirmation and fallback. This is a design preview, not an emulator or a native menu build; long-press settings are only a visual hint here.

## Recovered source and compatibility findings

The native menu source is available in [hmofet/netboot at 6ccbfdd](https://github.com/hmofet/netboot/tree/6ccbfdd000e705678ee422ebe972c2fccce40693/homebrew/netbootmenu). Source/assets are now vendored under `native/netbootmenu/` with original hashes and license/font notices. No replacement has been installed on the cabinet. The root [LICENSE](https://github.com/hmofet/netboot/blob/6ccbfdd000e705678ee422ebe972c2fccce40693/LICENSE) is the Unlicense.

- `main.c` initializes a 640x480 framebuffer, fonts, sprites and the host communication handler.
- `screens.c` owns `main_menu()`: cursor movement, title drawing and `MESSAGE_SELECTION`. Short Start release selects; holding Start leads to game settings. The artwork panel belongs in this rendering path, preserving the control/settings behavior.
- `config.c` reads configuration from `0x0D000000`; `config.h` defines a packed 136-byte game record matching WiPi's name/serial/index layout. Existing selection/settings/progress message IDs match the WiPi host's corresponding IDs.
- The recovered source's configuration lacks WiPi's `sram_save` word at byte 32. This shifts all following calibration/font/player fields by four bytes. Both sides use a 64-byte transmitted configuration area, so checking total payload length alone would miss the incompatibility. A packed-field offset comparison gives:

| Field | Recovered renderer offset | WiPi host offset |
| --- | --- | --- |
| SRAM save | Absent | 32 |
| First joystick calibration byte | 32 | 36 |
| Fallback font offset | 44 | 48 |
| Fallback font size | 48 | 52 |
| Forced player count | 52 | 56 |

The unmodified recovered renderer also lacks the host's `0x2003`/`0x2004` SRAM exchange handlers. Rebuilding it unchanged would risk misreading configuration and losing SRAM functionality. The new native baseline corrects the offsets above, reserves the full 64-byte area and adds those handlers with exact-size/enable checks. Host/C round-trip and fake SRAM tests pass; this does not verify battery SRAM or game behavior on hardware. Other inspected surviving forks generally carry the same older layout; none inspected supplied a verified exact installed-version match.

The Makefile expects `${NAOMI_BASE}/tools/Makefile.base`, SH-4 tools, libnaomimessage, FreeType, bzip2, zlib and libpng. An isolated container builder now supplies them, with pinned source archives and compiler distribution, and produces a valid little-endian SH-4 executable and Naomi ROM. Build instructions and limits are in `native/README.md`. WiPi's working host script and default menu selection are unchanged.

Next native milestone: runtime validation of the compiled text baseline's controls, settings and SRAM behavior. Local configuration/SRAM proofs and cross-compilation are complete; emulator/cabinet acceptance remains pending before the five-game native artwork proof.

## Evidence from this fork

- `sbin/piforce/singleboot.py` starts `menulauncher.py` for the menu default. In default mode, that script invokes `dm_netboot/netdimm_menu`, optionally with persistent replay behavior.
- `dm_netboot/scripts/netdimm_menu.py` reads the catalog, filters installed/enabled entries and orientation, sorts titles, then appends configuration to a Naomi menu ROM and sends it to the NetDIMM. The menu program runs on Naomi, separately from the Pi's web interface.
- Each current game record has a 128-byte name, four-byte serial and four-byte index. Configuration also supports settings and an optional fallback font, but no artwork field. The script handles menu selection/settings messages and sends the chosen game. Replacing this flow with a browser would require a different video/input architecture.
- `var/www/html/gamelist.php` obtains artwork filenames from `romsinfo.csv` column index 2 and titles from index 4. The repository's `var/www/html/images` is a symlink to `/boot/config/images`. This provides a candidate mapping to reuse, not proof that every image is present or suitable for the CRT. Do not commit cabinet assets automatically.
- The shipped `sbin/piforce/dm_netboot/homebrew/netbootmenu/` tree contains the original `netbootmenu.bin`, `.bin.dark` and `.bin.light`. Experimental renderer source/build rules are separate under `native/`; switching shipped binaries does not supply a game-artwork protocol.
- The public DragonMinded/netboot source URL returned HTTP 404 through both the GitHub connector and CLI during the initial investigation. Search results still reference it, so recheck availability rather than assuming permanent removal. The renderer was subsequently recovered through hmofet/netboot as described above; exact installed-version compatibility remains unverified.

## Platform support and limits

At inspected [libnaomi revision c840eb8](https://github.com/DragonMinded/libnaomi/tree/c840eb85384725182392ee3361706e80ae4ca4c0):

- The [sprite example](https://github.com/DragonMinded/libnaomi/blob/c840eb85384725182392ee3361706e80ae4ca4c0/examples/spritetest/main.c) initializes video, loads image textures and changes pages using JVS joystick/start input.
- Its [Makefile](https://github.com/DragonMinded/libnaomi/blob/c840eb85384725182392ee3361706e80ae4ca4c0/examples/spritetest/Makefile) converts PNG assets to RGBA4444 for the Naomi build. Phone images cannot simply be linked as web URLs inside the existing payload.
- The [toolchain instructions](https://github.com/DragonMinded/libnaomi/blob/c840eb85384725182392ee3361706e80ae4ca4c0/README.md) describe the SH-4 build environment, graphics, input and NetDIMM host communication.

These establish platform capability, not compatibility with the installed menu binary/protocol. Actual resolution/layout, available memory, artwork conversion, menu transfer time, rendering performance and physical JVS behavior need verification. Images increase the payload; load only visible images as textures rather than assuming the full catalog fits in video memory.

## Recommended first design

Start with a readable game list plus one large artwork/title panel for the highlighted game, a clear selection highlight and button hints. Up/down changes selection, the preview follows it, and the cabinet's confirm control launches the chosen game. Missing artwork falls back to the title. This aims for the phone's game-and-image presentation while fitting a landscape CRT and joystick navigation.

A small card grid is an alternative for a later mock-up; the phone's long portrait layout may not be readable unchanged. Filters, animation and video previews are separate proposals. Keep a text-menu fallback and preserve enabled-game/orientation selection, custom entries, settings/SRAM behavior, Single Boot and the existing transfer lifecycle. Browsing must not reboot Naomi or start a game upload on every selection change.

## Post-baseline check: game details, video and CRT experience

The user also requests a selected-game view inspired by the phone's Border Down screen: title, clear launch action, video preview and information below it. Record this as a feasibility/experience check **after the native baseline is accepted**, not part of the current baseline implementation. No native video playback or performance claim has been demonstrated.

The information already exists in the web catalog path. `var/www/html/gamelist.php` reads `romsinfo.csv` indices 0 (system), 3 (video filename), 4 (title), 6 (manufacturer), 7 (year), 8 (genre), 10 (orientation) and 11 (controls). It displays the clip through a browser `<video>` element using an MP4 file under `/videos/`. Reuse that canonical metadata rather than maintaining another catalog. The native payload currently carries none of these details beyond the title/serial/index; it needs a bounded, compatible extension before the native menu can display them.

The phone's browser performs video decoding. The native baseline has text/sprite rendering and no movie playback path, so copying an MP4 filename does not provide playback. Possible approaches to evaluate include a short preconverted frame sequence or a supported native decoder. Neither approach is selected yet. Preconversion on the host can avoid runtime transcoding, but frames consume storage, memory and transfer bandwidth; compression trades some of that for decoding work. More embedded media also increases the menu upload payload. Do not promise zero startup cost or unchanged responsiveness without measurements.

### CRT and control checks

- Design for the native 640x480, 4:3 view, with safe margins for the actual CRT's overscan. Keep the game title, preview and compact information below it readable at normal cabinet viewing distance. Use large text, clear contrast, visible selection/focus and wrapping for long titles/values; avoid shrinking a phone table to fit.
- Preserve the preview's aspect ratio, including vertical games within the landscape display. Keep video timing/output at the configured 31 kHz mode: opening, changing or closing a preview must not cause a reset, blanking or sync reacquisition.
- Make details and Back navigable with the physical joystick/buttons, retain the list position when returning, and keep quick game launch available. Choose the details control after reviewing the existing short-Start launch and long-Start settings mapping; do not silently replace those actions or require touch input.
- Show the title/information and a still image immediately. Evaluate a muted preview only once selection settles or details are opened, rather than decoding clips while rapidly scrolling. Launch and Back must respond immediately and stop media work; video must never become a mandatory wait before launching.
- Missing, unsupported or corrupt media must fall back to artwork/title and usable launch controls. Metadata must remain available independently of video; clip failure must not trigger another transfer or block selection.

### Performance experiment and acceptance record

1. Record the accepted text/artwork baseline first: menu payload bytes and upload/startup time, navigation/input response, frame timing, and RAM/texture memory use. Compare the same catalog and launch path on the same cabinet, keeping Single Boot and reset behavior fixed.
2. Add information below a still preview first and measure its cost. Then try one small muted local clip. An initial test could use roughly 320x240 at 10–15 fps for 5–10 seconds; those are experiment parameters, not a promised supported format or final quality target. Establish a memory/payload budget before choosing frame sequences versus a decoder, and do not preload the full video library into RAM/VRAM.
3. Test rapid selection changes, entering/exiting details, repeated preview loops and Launch during playback. Measure dropped frames, frame-time spikes, input delay, peak/leaked memory, menu upload/startup cost and game-launch timing. Also check long/missing metadata, absent/corrupt clips, vertical content and CRT edge/text readability.
4. Record the before/after figures and user-observed responsiveness. Only adopt video if startup, browsing and launching meet an explicitly reviewed performance budget and the CRT view is readable. If video adds a noticeable wait or compromises controls, retain the still-image/details view and leave video deferred; the phone can keep its existing video view.

This check does not authorize installing codecs, changing Pi video wiring, replacing the menu or collecting/copying cabinet media. Scope any implementation after baseline acceptance, with fixtures first and an approved, backed-up hardware comparison.

## Staged investigation and acceptance

1. Source recovery, layout/SRAM adaptation, local C tests and native cross-build are complete for a candidate text baseline, not an exact copy of the installed version. Establish runtime behavior before modifying the interface. Do not treat binary patching or an installed-system toolchain upgrade as approved.
2. Review the supplied CRT-proportioned browser layout preview, including long titles and missing artwork. A small grid can be compared later if desired. Preserve video wiring; no Pi kiosk is needed for this route.
3. Build an isolated five-game proof with artwork embedded in the menu payload, prepared on the host. Preserve sender behavior and game IDs. Include bounds/version checks for new data and retain the original menu for rollback. Test missing/invalid artwork, memory limits and selection-to-game mapping.
4. Check rendering and controls in a suitable Naomi emulator where supported, then prepare a backed-up cabinet comparison for approval. Emulator success does not establish physical JVS, CRT or NetDIMM behavior.
5. On approved hardware testing, check startup time, browsing responsiveness, title readability, correct game launch, settings and Single Boot/OSM behavior. Expand the catalog only after the proof passes. Coordinate this after acceptance of the current loading-status enhancement.
6. After baseline acceptance, apply the game-details/video checks above as a separate feasibility experiment. Keep the still-image path usable regardless of the video result.

An illustrated menu does not resolve the separate [CRT signal-loss clicking investigation](crt-sync-follow-up.md); the game-start reset remains. It also does not coordinate independent OSM and phone transfers. Preserve that restriction until coordination is separately designed.
