## Maintained fork

This fork preserves the tested OSM default-save correction and ordinary-upload guard from a WiPi64 installation. The first enhancement adds asynchronous loading status, busy handling and failure reporting while retaining the existing transfer tools and Single Boot behavior.

- [Baseline and preserved behavior](docs/fork-baseline.md)
- [Loading status: behavior, tests and deployment](docs/loading-status.md)
- [Deferred CRT signal-loss clicking investigation](docs/crt-sync-follow-up.md)
- [Agent instructions: architecture, invariants and verification](AGENTS.md)

The enhancement is tracked in [PR #1](https://github.com/wassoufa/WiPiNetbooter64/pull/1) and has not been deployed to the cabinet. Merging source does not install it on the Pi or establish hardware acceptance. No personal cabinet settings, credentials, logs or ROMs are added by these changes.

### Current status

- **Fork created:** [wassoufa/WiPiNetbooter64](https://github.com/wassoufa/WiPiNetbooter64), based on cassianoperin's 64-bit fork. The public upstream is older than the installed `wipi 0.22-0` package; it is not a complete copy of that installation.
- **Baseline fixes preserved:** saving the OSM default retains all eight NetDIMM configuration fields, and the ordinary loader uses a per-target lock to prevent overlapping uploads from duplicate requests. These fixes have been tested on the cabinet.
- **First enhancement implemented:** [PR #1](https://github.com/wassoufa/WiPiNetbooter64/pull/1) adds preparation, upload, game-start and error states. A live upload can wait at 0% without being declared failed. Repeated requests follow the active upload; status polling, refresh and status retries never resend a game. Old completion records are ignored for a new launch.
- **Offline checks pass:** loader concurrency/failure tests, status-helper tests, PHP HTTP tests with a fake sender, OSM serialization regression checks and PHP syntax checks. Successful sender exit means the transfer and game-start command completed; playable gameplay still needs cabinet confirmation.
- **Hardware acceptance pending:** the first enhancement has not been installed on the Pi. The cabinet retains the previously tested fixes.

### Rollout plan

1. Use PR #1 as the reviewed source baseline. Its offline checks pass; cabinet deployment and acceptance remain separate. Source research and offline design previews can proceed while hardware testing is pending.
2. With approval and no active transfer, back up the affected Pi files and their ownership/permissions, verify the rollback archive, then install the helpers before their callers. Follow the [deployment and rollback instructions](docs/loading-status.md#deployment-and-acceptance--not-yet-performed).
3. Test one normal phone upload, a duplicate request while busy, a subsequent different game, and switching from the arcade menu to the phone after the menu transfer finishes. Confirm that a 0% pause produces a waiting explanation and one transfer. Check normal Single Boot startup in a user-coordinated test.
4. Record the observed result on Naomi as well as the logs. Resolve any regression before deploying further enhancements. Keep failure/interruption tests in fixtures rather than deliberately disrupting a live upload.
5. Add later features separately, with focused offline checks and a backed-up cabinet test for each change.

Preserve Single Boot, the OSM repair, upload locking, existing network settings, game files and optional control/card behavior. This enhancement does not change reset timing or NOW LOADING behavior. The ordinary-loader lock does not coordinate independent OSM or standalone transfers: finish the arcade-menu transfer before launching from the phone.

### Enhancement roadmap

The fork review identified the following candidates. Only the first enhancement and its launch validation are implemented; later product changes remain proposals to scope and test individually.

| Order | Enhancement | Status and intended scope |
| --- | --- | --- |
| 1 | Clear loading, busy and failure reporting | Implemented in PR #1; cabinet acceptance pending. Known-ROM selection, configured-target compatibility checks and individual shell-argument quoting are included. |
| 2 | Optional phone-friendly launcher | Proposed next after loading is stable: artwork grid, favourites, recent games, game details and an explicit launch button, using the existing loader and status flow. Keep the configuration pages and CRT menu available. |
| 3 | Search and touch controls | Proposed: title search, system/genre/orientation/control filters and larger touch controls within the chosen launcher. Evaluate one interface rather than combining complete interfaces from different forks. |
| 4 | Bulk game-list management | Proposed: enable/disable selected games without deleting ROMs, using locked, atomic CSV updates that preserve metadata. Distinguish browser-only hiding from changes that affect OSM; review Naomi/Naomi 2 filtering separately. |
| 5 | Artwork and catalog corrections | Optional: compare individual artwork files and catalog rows with installed filenames; preserve custom entries such as the CRT tester. Themes are optional polish. |

Additional investigation: [game artwork in the default arcade menu](docs/illustrated-osm-investigation.md), with joystick selection and a large image/title preview inspired by the phone interface. Candidate renderer source has been recovered, but its configuration/SRAM behavior differs from WiPi. An [offline interactive layout preview](docs/previews/illustrated-osm.html) is available; a compatible native build and cabinet test remain pending.

Sources for selective adaptation include [WiPiNetbooter-NG](https://github.com/metisnc/WiPiNetbooter-NG/tree/23412c084e5fc19d920308f4a2d1566c59181ce2), [thegoodguys80's interface work](https://github.com/thegoodguys80/WiPiNetbooter/tree/38fb4d42cadbde53ddb2d9c4639a84c6b6fafa13) and [AyanamiRei1's artwork/catalog changes](https://github.com/AyanamiRei1/WiPiNetbooter/tree/03282df71e0cf12a1361cbdc748f7b2f12008c77). Their alternative backends, configuration writers and full images need separate compatibility review before adoption. A phone-only launcher does not require a kiosk/display installer or an OS upgrade.

### Deferred CRT investigation

The Toshiba PD2367 is already running at 31 kHz. Clicking occurs when Naomi's video signal disappears during a reset and returns. Sync loss/reacquisition is the working explanation; chassis damage has not been established.

Later, compare the picture interruptions and click counts for arcade-menu and phone launches. The sender's `--disable-now-loading` option can skip the preliminary loading request, but the final game-start reset remains. Any controlled comparison needs a backup, approval and checks of loading compatibility and timing. No CRT-related code or settings changes have been made. See the [recorded follow-up](docs/crt-sync-follow-up.md).

# WiPiNetbooter64

Port of chunksin's WiPiNetbooter to run into an updated Debian Trixie 64 bits linux.

## Raspberry PI 3B, 4 and 5 (Debian Trixie)

Full image download link: (https://mega.nz/folder/D4hyHACR#WRjBIlZJ9JPfDcaYOz9LWQ/folder/j0oAQRLC)

<br>Changes:
1. 64 bits Operating System (Debian Trixie manually created minimal image to fit into an 32GB SD card)
2. Fully functional integration between FFB Controller Hardware, OpenJVS, OpenFFB and New-lg4ff wheel driver for force feedback events on supported games
3. New wipi 64 bits package
4. Logitech New-lg4ff driver updated to suport FFB on Logitech wheels (https://github.com/berarma/new-lg4ff)
5. Added OpenJVS Logitech G923 device map (/etc/openjvs/devices/logitech-g923-racing-wheel-for-playstation-4-and-pc)
6. Fixed WiPi OpenFFB Update Menu (/var/www/html/updateopenffb.php)
7. Fixed WiPi OpenJVS Control and enabled log to /var/log/openjvs/openjvs.log (/var/www/html/launchopenjvs.php)
8. Added a simple script to start and stop DragonMinded's Web App (/root/dm_netboot.sh - requires uncompressed roms)
9. Enabled wipiloader.py log for openffb to /var/log/openffb/openffb.log (/sbin/piforce/wipiloader.py)
10. Created an update script for DragonMinded Netboot (/root/update-dm_netboot.sh)
11. Compiled Bobby Dilley's Cycraft Emulator for 64bits (/usr/lib/cycraft)
12. Added Street Fighter Alpha 3 Upper (USA region hack) to gamelist
13. Fixed card emulator for F-Zero (/var/www/html/launchcard.php)
14. Created a script to set the correct IP for Mario Kart GP camera on eth0 after game is launched (/root/mariokart_camera.sh)
15. Corrected openjvs game mapping for king-of-route-66 (romsinfo.csv)
16. Compiled wipi64-mjpg-streamer for 64 bits with necessary api code customization for Mario Kart Camera
17. Using OpenJVS update for new GPIO logic by Fredobedo (https://github.com/Fredobedo/OpenJVS/)
18. Single image that supports both raspberry pi 4 and 5 (not tested on 3 yet)
19. SD card interchangeable between rpi 4 and rpi5 (automatically updates serial ports on all scripts)
20. Full support for Naomi, Naomi 2, Triforce and Chihiro boards
21. Support for Argon NVMe SSDs
22. Backup Manager to save and restore Wipi configurations
23. Raspberry PI 3B hardware (OpenJVS Hat Serial port for card emulator will not work due to uart limitations)
24. New ROM Hack Outrun 2 SP with the advertisement mode and ending game sprites url fixed to new Online Ranking (from outrun.jp to  wipi64.com)

TODO:
1. Add an apt source to update wipi packages
2. Make network modes to use NetworkManager

## Card Reader Emulator Pinouts

### Sega Naomi / Naomi2

Supported games: Initial D, Initial D 2, Initial D 3

**OpenJVS Hat** | **USB to RS232 Adapter**
:-------------------------:|:-------------------------:
<img width="430" alt="horizontal" src="https://github.com/cassianoperin/WiPiNetbooter64/blob/master/%23pinouts/card_pinout_naomi_openjvs_hat.png">  |  <img width="415" alt="vertical" src="https://github.com/cassianoperin/WiPiNetbooter64/blob/master/%23pinouts/card_pinout_naomi_usb_rs232_adapter.png">

### Sega Triforce

Supported games: F-Zero AX, Mario Kart Arcade GP, Mario Kart Arcade GP 2

**OpenJVS Hat** | **USB to RS232 Adapter**
:-------------------------:|:-------------------------:
<img width="430" alt="horizontal" src="https://github.com/cassianoperin/WiPiNetbooter64/blob/master/%23pinouts/card_pinout_triforce_openjvs_hat.png">  |  <img width="415" alt="vertical" src="https://github.com/cassianoperin/WiPiNetbooter64/blob/master/%23pinouts/card_pinout_triforce_usb_rs232_adapter.png">

### Sega Chihiro

Supported games: Wangan Midnight Maximum Tune, Wangan Midnight Maximum Tune 2

**OpenJVS Hat** | **USB to RS232 Adapter**
:-------------------------:|:-------------------------:
<img width="430" alt="horizontal" src="https://github.com/cassianoperin/WiPiNetbooter64/blob/master/%23pinouts/card_pinout_chihiro_openjvs_hat.png">  |  <img width="415" alt="vertical" src="https://github.com/cassianoperin/WiPiNetbooter64/blob/master/%23pinouts/card_pinout_chihiro_usb_rs232_adapter.png">

## MIDI Pinouts for FFB Controller (Sega Naomi/Naomi2 and Chihiro)
https://github.com/Fredobedo/openFFB


## Raspberry Pi based Netbooter for Sega Naomi/Chihiro/Triforce arcade boards

<b>Instruction manual:</b> https://drive.google.com/file/d/19VvqMnIEYF-vSp-SlMRuhi5AT0qcu-_e/view?usp=drivesdk<br>
<p>This version of the Pi Netbooter code is a scratch rewrite of the original solution written by devtty0 and has been enhanced with a new user interface and richer functionality. It has full support for all netbootable Sega arcade ROMs for the Naomi, Naomi2, Triforce, Chihiro and the Atomiswave conversions made possible by Darksoft. This version also includes the card reader emulator code for games that support it, the original python scripts were written by Winteriscoming on the arcade-projects.com forums and have been adapted for use in a web interface. The entire netbooting suite of scripts including the on screen menu and server mode was written by DragonMinded and integrated into WiPi.</p>
<p>You will need:</p>
<p>A Raspberry Pi v3B, 3B+ or 4B and microSD Card - 32GB Class 10 card recommended</p>
<p>A Naomi, Naomi2, Triforce or Chihiro with a netdimm running firmware 3.03 or greater</p>
<p>A standard network cable and 5v power source for the Pi &ndash; you can make a custom cable to draw power directly from the system</p>
<p>A Web Browser :)</p>
<p>Optional but recommended: a zero security pic chip</p>
<p>Optional: a Trendnet TU-S9 USB-Serial adaptor and custom serial cable for the Card Emulator</p>
<p>Optional: an FTDI based RS485 to USB adaptor for OpenJVS (see <a href="https://github.com/OpenJVS/OpenJVS">https://github.com/OpenJVS/OpenJVS</a> for more information)</p>
<p>Optional: OpenJVS Pi HAT (see <a href="https://github.com/OpenJVS/OpenJVS">https://github.com/OpenJVS/OpenJVS</a> for more information)</p>
<p>Optional: ACS ACR122U NFC Card Reader</p>

