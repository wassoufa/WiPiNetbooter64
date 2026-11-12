# Existing SH-4/newlib compiler distribution. Runs only inside the builder.
FROM rattboi/naomi-build@sha256:f8fb420595d945d3379f51f2675e6390e4decbb622b8c8bea79cc8eeeee2f83e
RUN sed -i 's|http://dl-cdn|https://dl-cdn|' /etc/apk/repositories && \
    apk add --no-cache py3-pip py3-pillow autoconf automake
COPY requirements.txt /tmp/requirements.txt
RUN pip3 install --no-cache-dir -r /tmp/requirements.txt
COPY .cache/ /tmp/sources/
COPY sources.json /tmp/sources.json
RUN python3 -c 'import json,hashlib,pathlib; files=json.load(open("/tmp/sources.json")); [(None if hashlib.sha256((pathlib.Path("/tmp/sources")/f["name"]).read_bytes()).hexdigest()==f["sha256"] else exit("Archive checksum mismatch")) for f in files]'
RUN mkdir /build && tar -xzf /tmp/sources/libnaomi.tar.gz -C /build --strip-components=1 && \
    mkdir -p /build/3rdparty/zlib/download /build/3rdparty/libbz2/download /build/3rdparty/libpng/download /build/3rdparty/freetype/download && \
    cp /tmp/sources/zlib-1.2.13.tar.gz /build/3rdparty/zlib/download/ && \
    cp /tmp/sources/bzip2-1.0.8.tar.gz /build/3rdparty/libbz2/download/bzip2_1.0.8.orig.tar.gz && \
    cp /tmp/sources/libpng-1.6.37.tar.gz /build/3rdparty/libpng/download/ && \
    cp /tmp/sources/freetype-2.10.2.tar.gz /build/3rdparty/freetype/download/
SHELL ["/bin/bash", "-c"]
RUN source /opt/toolchains/naomi/env.sh && \
    make -C /build/libnaomi -j4 VENV_PYTHON3=/usr/bin/python3 DATE='printf 20261113' install && \
    make -C /build/3rdparty/zlib -j1 VENV_PYTHON3=/usr/bin/python3 install && \
    make -C /build/3rdparty/libbz2 -j1 VENV_PYTHON3=/usr/bin/python3 install && \
    make -C /build/3rdparty/libpng -j1 VENV_PYTHON3=/usr/bin/python3 install && \
    make -C /build/3rdparty/freetype -j1 VENV_PYTHON3=/usr/bin/python3 install && \
    make -C /build/libnaomi clean && \
    make -C /build/libnaomi -j4 VENV_PYTHON3=/usr/bin/python3 DATE='printf 20261113' install && \
    make -C /build/libnaomi/message -j4 VENV_PYTHON3=/usr/bin/python3 DATE='printf 20261113' install && \
    mkdir -p /opt/toolchains/naomi/tools && \
    cp /build/Makefile.external.base /opt/toolchains/naomi/tools/Makefile.base && \
    cp /build/Makefile.shared /build/naomi.ld /build/aica.ld /build/tools/*.py /opt/toolchains/naomi/tools/ && \
    pip3 freeze > /opt/toolchains/naomi/python-packages.txt
WORKDIR /src
ENTRYPOINT ["/bin/bash", "-c", "source /opt/toolchains/naomi/env.sh; exec \"$@\"", "--"]
CMD ["make", "VENV_PYTHON3=/usr/bin/python3"]
