FROM debian:trixie
ARG optical_gid
ARG uid=1000

RUN apt-get update && apt-get install --no-install-recommends -y \
    cd-paranoia \
    cdrdao \
    python3-cdio \
    bzip2 \
    curl \
    eject \
    flac \
    git \
    libdiscid0 \
    libtool \
    locales \
    make \
    pkgconf \
    python3-dev \
    python3-musicbrainzngs \
    python3-mutagen \
    python3-pil \
    python3-pip \
    python3-ruamel.yaml \
    python3-setuptools \
    libsndfile1-dev \
    libiso9660-dev \
    libcdio-dev \
    sox \
    swig \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# add user (+ group workaround for ArchLinux)
RUN useradd -m worker --uid ${uid} -G cdrom \
    && if [ -n "${optical_gid}" ]; then groupadd -f -g "${optical_gid}" optical \
    && usermod -a -G "${optical_gid}" worker; fi \
    && mkdir -p /output /home/worker/.config/whipper \
    && chown worker: /output /home/worker/.config/whipper
VOLUME ["/home/worker/.config/whipper", "/output"]

# setup locales + cleanup
RUN echo "LC_ALL=en_US.UTF-8" >> /etc/environment \
    && echo "en_US.UTF-8 UTF-8" >> /etc/locale.gen \
    && echo "LANG=en_US.UTF-8" > /etc/locale.conf \
    && locale-gen en_US.UTF-8

# Trixie-shipped setuptools doesn't work, need to upgrade...
# Pin setuptools_scm as versions 10>= require packaging>=26.2 which conflicts with
# the version from debian.
RUN pip install -U setuptools discid "setuptools_scm<10" --break-system-packages

# install whipper
RUN mkdir /whipper
COPY . /whipper/
RUN cd /whipper && pip install . --break-system-packages \
    && rm -rf /whipper \
    && whipper -v

ENV LC_ALL=en_US.UTF-8
ENV LANG=en_US
ENV LANGUAGE=en_US.UTF-8
ENV PYTHONIOENCODING=utf-8

USER worker
WORKDIR /output
ENTRYPOINT ["whipper"]
