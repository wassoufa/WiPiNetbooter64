# B4 memory diagnostic: offline readiness

This is an isolated diagnostic, not the installed menu or a leak-free acceptance result. Read the [B4 plan](../../docs/native-memory-soak-plan.md) and [offline result](../../docs/results/2026-11-14-memory-offline.md). Canonical `native/netbootmenu/` sources and the `45ef4f20…` ROM pin are unchanged. No new dependencies, emulator message bridge or cabinet telemetry service are introduced.

## Build and focused checks

From the repository root, with the existing pinned builder image available:

```sh
python3 -B tests/test_memory_diagnostic.py
python3 -B tests/test_native_menu.py
python3 -B native/emulator/build-memory-diagnostic.py
git diff --check
```

The builder uses a read-only source mount, networking disabled and disposable build storage. It copies the canonical menu, adds the sampler and inserts guarded observation hooks into that copy only. Exact patch anchors/screen IDs must match. Output is ignored `native/out/memory-diagnostic/`: bare diagnostic, synthetic configured ROM, matching ELF, source patch, compiler/package/image identity and hash manifest. The synthetic configured ROM is for local testing; never send its invented catalog to Naomi. A later approved cabinet test must use the bare diagnostic with freshly reviewed installed-host configuration and a private SRAM-OFF clone.

For host sanitizer checks where supported:

```sh
NATIVE_TEST_CFLAGS='-g -O1 -fno-omit-frame-pointer -fsanitize=address,undefined' \
  ASAN_OPTIONS='detect_leaks=0:halt_on_error=1' \
  UBSAN_OPTIONS='halt_on_error=1:print_stacktrace=1' \
  python3 -B tests/test_memory_diagnostic.py
```

The recorded macOS run supports ASan/UBSan but not leak sanitizer. `detect_leaks=0` is not a leak check. The fixture uses target-shaped allocator mocks to verify observer ownership/state and failure handling, not real target allocation behavior.

## Collection policy and metric coverage

- Observe the existing control snapshot and actual rendered/next screen; no extra input poll or overlay. Sample only stable main/settings states after 120 consecutive completed quiet frames. The hook runs after vblank and existing frame/profile accounting. Held Start, mapped input events, transitions or message activity reset settling; unsupported settings departure stops collection.
- Require no pending send/receive packets and no send/receive in progress. Read packet counters before/after allocator snapshots; reject a changed snapshot. A previous diagnostic packet must drain before another stable interval. This bounds observer interference, not every possible concurrent-allocation race.
- Read counters before formatting/queuing output. Use checked `message_send(0x7FFE, ...)`, the existing host-stdout message type, because the ordinary printf redirect hides queue failures. No new message type or host modification is required. The stack buffer is copied by the packet library. Formatting or send failure stops sampling without retry.
- Calibrate heap reporting once at the first stable boundary: allocate/free 4,096 bytes, require an increase during allocation and return to the prior live-use count with unchanged packet counters. Free the probe on all paths, then settle again. This observer allocation can retain allocator arena space; failed calibration leaves heap validity false and capture unusable.
- Record `mallinfo()` heap and `ta_texture_mallinfo()` managed-texture `arena/uordblks/fordblks` in bytes. Validity requires initialized/plausible counters. All-zero preinitialization is unavailable, not zero-use proof. Heap includes ordinary allocated metadata/cache objects; texture statistics exclude reserved framebuffers/TA working storage, sound RAM and other memory outside that allocator. They do not measure fragmentation or all stack/static storage.
- Use one owned `timer_start(UINT32_MAX)` handle and non-destructive `timer_elapsed()`, including observer work. This is guest elapsed time, separate from summed draw/profile time and host UTC. Runs must finish well below the roughly 71.6-minute 32-bit range. A backward reading or maximum value stops collection; the pinned timer casts before clamping, so this is not a general multi-wrap guarantee. Stop paths release the handle.
- Emit transition records plus sparse idle records after at least 60 guest seconds since the prior sample. At most 96 records; the final limit event means incomplete/unusable, not success. The cap and one-at-a-time drain gate bound queued observer data.

## Capture and interpretation

The existing installed verbose host can carry these records into its fixed menu log; preserve that log and merged raw console before another invocation overwrites them. Confirm the capture path on the actual target before any measured cycles. Stock raw-ROM Flycast cannot provide that host/settings bridge. The offline mocked capture proves sampler-to-decoder format handling, not a cabinet message exchange.

A record is one newline-terminated CSV line, optionally prefixed by the host logger:

```text
B4M1,sequence,cycle,event,screen,game,guest_us,heap_valid,heap_arena,heap_used,heap_free,texture_valid,texture_arena,texture_used,texture_free
```

Events are 1 initial main, 2 settings, 3 discard return, 4 idle and 5 unusable limit. Numeric game IDs are run-specific. The decoder rejects malformed/truncated/unknown records, gaps/duplicates, invalid metrics, wrong state order, changing settings-game identity, insufficient trailing idle and limit overflow. Initial main selection may differ from the chosen settings game.

For the proposed two warm-up plus 20 measured cycles and 15 trailing guest-minute samples:

```sh
python3 -B native/diagnostics/decode-memory.py /absolute/private/capture.log \
  --expect-cycles 22 --min-idle 15 > /absolute/private/decoded.json
```

The command validates declared capture structure. It does not award a soak PASS, verify literal discard inputs/forbidden protocol absence, establish host elapsed time, classify memory trends or prove physical rollback. Wait for each host-confirmed settings/discard sample before the next Start input. Evaluate identical post-cleanup states after warm-up using live-use `uordblks`; retain `arena/fordblks` as context. Apply the plan's predeclared trend/stop rules and report actual host and guest duration separately. A bounded pass means no leak detected in the exercised paths/duration.
