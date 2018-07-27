FROM debian:buster

RUN apt-get update \
  && apt-get install -y cdrdao python-gobject-2 python-musicbrainzngs python-mutagen python-setuptools \
  python-cddb python-requests libsndfile1-dev flac sox \
  libiso9660-dev python-pip swig make pkgconf \
  libiso9660-dev eject locales \
  autoconf libtool curl \
  && pip install pycdio

# libcdio-utils, libcdio-dev are actually required

RUN curl -o 'libcdio-0.94.tar.gz' 'https://ftp.gnu.org/gnu/libcdio/libcdio-0.94.tar.gz'
RUN printf '96e2c903f866ae96f9f5b9048fa32db0921464a2286f5b586c0f02699710025a  libcdio-0.94.tar.gz' | sha256sum -c
RUN tar xf libcdio-0.94.tar.gz && cd libcdio-0.94/ \
&& autoreconf -fi \
&& ./configure --disable-dependency-tracking --disable-cxx --disable-example-progs --disable-static \
&& make install

# Install cd-paranoia from tarball
RUN curl -o 'libcdio-paranoia-10.2+0.94+2.tar.gz' 'https://ftp.gnu.org/gnu/libcdio/libcdio-paranoia-10.2+0.94+2.tar.gz'
RUN printf 'd60f82ece97eeb92407a9ee03f3499c8983206672c28ae5e4e22179063c81941  libcdio-paranoia-10.2+0.94+2.tar.gz' | sha256sum -c
RUN tar xf libcdio-paranoia-10.2+0.94+2.tar.gz && cd libcdio-paranoia-10.2+0.94+2/ \
&& autoreconf -fi \
&& ./configure --disable-dependency-tracking --disable-example-progs --disable-static \
&& make install

RUN ldconfig

# install whipper
RUN mkdir /whipper
COPY . /whipper/
RUN cd /whipper/src && make && make install \
  && cd /whipper && python2 setup.py install \
  && rm -rf /whipper

# add user
RUN useradd -m worker -G cdrom \
  && mkdir -p /output /home/worker/.config/whipper \
  && chown worker: /output /home/worker/.config/whipper
VOLUME ["/home/worker/.config/whipper", "/output"]

# setup locales + cleanup
RUN echo "LC_ALL=en_US.UTF-8" >> /etc/environment \
  && echo "en_US.UTF-8 UTF-8" >> /etc/locale.gen \
  && echo "LANG=en_US.UTF-8" > /etc/locale.conf \
  && locale-gen en_US.UTF-8 \
  && apt-get clean && apt-get autoremove -y

ENV LC_ALL=en_US.UTF-8
ENV LANG=en_US
ENV LANGUAGE=en_US.UTF-8
ENV PYTHONIOENCODING=utf-8

USER worker
WORKDIR /output
RUN whipper -v
ENTRYPOINT ["whipper"]
