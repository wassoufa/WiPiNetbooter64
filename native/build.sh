#!/bin/sh
# Build an experimental menu locally. Never installs or sends anything to a Pi.
set -eu
task_root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
python3 "$task_root/native/build-env/fetch.py"
docker build --platform linux/amd64 -t wipi-native-builder:baseline "$task_root/native/build-env"
mkdir -p "$task_root/native/out"
docker run --rm --platform linux/amd64 --network none --read-only \
    --tmpfs /tmp:exec \
    -v "$task_root/native:/source:ro" \
    -v "$task_root/native/out:/out" \
    wipi-native-builder:baseline /bin/bash -ec '
        cp -R /source/netbootmenu /tmp/menu
        cd /tmp/menu
        make VENV_PYTHON3=/usr/bin/python3
        cp netbootmenu.bin build/naomi.elf /out/
        /opt/toolchains/naomi/sh-elf/bin/sh-elf-readelf -h build/naomi.elf > /out/elf-header.txt
        /opt/toolchains/naomi/sh-elf/bin/sh-elf-gcc --version > /out/compiler.txt
        cp /opt/toolchains/naomi/python-packages.txt /out/
        sha256sum netbootmenu.bin > /out/SHA256SUMS
        python3 /source/check-rom.py /out/netbootmenu.bin > /out/manifest.json
    '
docker image inspect --format '{{.Id}}' wipi-native-builder:baseline > "$task_root/native/out/builder-image-id.txt"
printf '%s\n' "Experimental artifacts: $task_root/native/out (not deployed)"
