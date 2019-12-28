FROM debian:buster

RUN apt-get update && apt-get install --no-install-recommends -y \
    autoconf \
    automake \
    cdrdao \
    bzip2 \
    curl \
    eject \
    flac \
    gir1.2-glib-2.0 \
    git \
    libdiscid0 \
    libiso9660-dev \
    libsndfile1-dev \
    libtool \
    locales \
    make \
    pkgconf \
    python3-dev \
    python3-gi \
    python3-musicbrainzngs \
    python3-mutagen \
    python3-pip \
    python3-requests \
    python3-ruamel.yaml \
    python3-setuptools \
    sox \
    swig \
    && apt-get clean && rm -rf /var/lib/apt/lists/* \
    && pip3 --no-cache-dir install pycdio==2.1.0 discid

# libcdio-paranoia / libcdio-utils are wrongfully packaged in Debian, thus built manually
# see https://github.com/whipper-team/whipper/pull/237#issuecomment-367985625
RUN curl -o - 'https://ftp.gnu.org/gnu/libcdio/libcdio-2.1.0.tar.bz2' | tar jxf - \
    && cd libcdio-2.1.0 \
    && autoreconf -fi \
    && ./configure --disable-dependency-tracking --disable-cxx --disable-example-progs --disable-static \
    && make install \
    && cd .. \
    && rm -rf libcdio-2.1.0

# Install cd-paranoia from tarball
RUN curl -o - 'https://ftp.gnu.org/gnu/libcdio/libcdio-paranoia-10.2+2.0.0.tar.bz2' | tar jxf - \
    && cd libcdio-paranoia-10.2+2.0.0 \
    && autoreconf -fi \
    && ./configure --disable-dependency-tracking --disable-example-progs --disable-static \
    && make install \
    && cd .. \
    && rm -rf libcdio-paranoia-10.2+2.0.0

RUN ldconfig

# add user
RUN useradd -m worker -G cdrom \
    && mkdir -p /output /home/worker/.config/whipper \
    && chown worker: /output /home/worker/.config/whipper
VOLUME ["/home/worker/.config/whipper", "/output"]

# setup locales + cleanup
RUN echo "LC_ALL=en_US.UTF-8" >> /etc/environment \
    && echo "en_US.UTF-8 UTF-8" >> /etc/locale.gen \
    && echo "LANG=en_US.UTF-8" > /etc/locale.conf \
    && locale-gen en_US.UTF-8

# install whipper
RUN mkdir /whipper
COPY . /whipper/
RUN cd /whipper && python3 setup.py install \
    && rm -rf /whipper \
    && whipper -v

ENV LC_ALL=en_US.UTF-8
ENV LANG=en_US
ENV LANGUAGE=en_US.UTF-8
ENV PYTHONIOENCODING=utf-8

USER worker
WORKDIR /output
ENTRYPOINT ["whipper"]
