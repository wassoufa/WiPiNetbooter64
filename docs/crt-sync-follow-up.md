CRT signal-loss clicking — deferred investigation

Cabinet: Sega New Net City, Toshiba PD2367 chassis. The user confirms Naomi is configured for 31 kHz. Clicking occurs as video/sync disappears during a Naomi restart and returns afterwards. The picture returns normally; repeated relay chatter/flicker was not reported.

Working interpretation: loss/reacquisition of sync, rather than a proven 15-to-31 kHz change. The click alone does not establish chassis damage; no hardware diagnosis or modification has been performed.

Installed-code finding: the phone sender requests NOW LOADING before upload, then reboots Naomi after upload. The supported --disable-now-loading option suppresses the preliminary request but retains the final reset. OSM already uses disable_now_loading=True for selected games. This is a candidate for a controlled comparison, not a proven way to remove every video interruption or startup delay.

When revisited:
1. Compare click counts and picture interruptions for OSM-selected versus phone-selected games.
2. Review compatibility of skipping NOW LOADING during game-to-game replacement.
3. Prepare a backed-up, approved test if appropriate; preserve Single Boot, the OSM repair and upload locking.
4. Record whether clicks, upload timing and successful game startup change. Do not bypass monitor relays/protection or make chassis modifications to suppress the sound.

No settings or code changes have been made for this item.

References:
- https://www.arcade-projects.com/threads/toshiba-tri-sync-pbxx-pdxx-pexx-notes-mods.21081/
- https://github.com/cassianoperin/WiPiNetbooter64/blob/master/sbin/piforce/dm_netboot/scripts/netdimm_send.py
