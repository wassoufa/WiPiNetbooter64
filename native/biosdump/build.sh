#!/bin/sh
# Uses the already prepared pinned native builder; no downloads or live operations.
set -eu
task_root=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
mkdir -p "$task_root/native/out/biosdump"
docker run --rm --platform linux/amd64 --network none --read-only --tmpfs /tmp:exec \
  -v "$task_root/native/biosdump:/source:ro" -v "$task_root/native/out/biosdump:/out" \
  wipi-native-builder:baseline /bin/bash -ec '
    cp -R /source /tmp/biosdump
    cd /tmp/biosdump
    make VENV_PYTHON3=/usr/bin/python3
    cp biosdump.bin build/naomi.elf /out/
    sha256sum biosdump.bin > /out/SHA256SUMS
    /opt/toolchains/naomi/sh-elf/bin/sh-elf-nm build/naomi.elf > /out/symbols.txt
  '
docker image inspect --format '{{.Id}}' wipi-native-builder:baseline > "$task_root/native/out/biosdump/builder-image-id.txt"
