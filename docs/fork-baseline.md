# Fork baseline

This fork starts from cassianoperin/WiPiNetbooter64. The cabinet installation inspected during development reports package wipi 0.22-0 on Debian 13 arm64; the public upstream repository is an older source snapshot, not an exact image of that package.

Two locally tested fixes are preserved:

- Expand the OSM default to menu,none,none when saving NetDIMM records. All eight fields, including cabinet orientation, remain in their expected positions.
- Use a nonblocking per-target lock before ordinary loader side effects. Duplicate requests are ignored while the active upload completes. Persistent Server Mode retains its own manager lifecycle.

The inspected installation's existing five-second OpenFFB startup delay is also retained. No cabinet configuration, credentials, logs or game files are copied into this branch.

The upload guard passed isolated concurrency tests and a live phone test: repeated web requests produced one sender, and the game started once. Repeated simultaneous cabinet cold starts remain a later hardware check.

The initial upload can pause below 1%. Tests observed different pause durations for the same ROM. This fork does not infer a failed transfer solely from a temporary 0% reading, and does not change reset timing or NOW LOADING behavior.

The CRT signal-loss clicking investigation is deferred; see crt-sync-follow-up.md. Features must preserve Single Boot, OSM, the ordinary-upload lock, configured network addresses and the existing game directory.
