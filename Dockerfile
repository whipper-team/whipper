FROM debian:stretch

RUN apt-get update
RUN apt-get install -y cdparanoia cdrdao python-gobject-2 python-musicbrainzngs python-mutagen python-setuptools \
  python-cddb python-requests libsndfile1-dev flac sox \
  libiso9660-dev python-pip swig make pkgconf \
  libcdio-dev libiso9660-dev libcdio-dev eject locales

RUN pip install --upgrade pip
RUN pip install pycdio==0.21

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

RUN echo "LC_ALL=en_US.UTF-8" >> /etc/environment \
  && echo "en_US.UTF-8 UTF-8" >> /etc/locale.gen \
  && echo "LANG=en_US.UTF-8" > /etc/locale.conf \
  && locale-gen en_US.UTF-8

ENV LC_ALL=en_US.UTF-8
ENV LANG=en_US
ENV LANGUAGE=en_US.UTF-8
ENV PYTHONIOENCODING=utf-8

USER worker
WORKDIR /output
RUN whipper -v
ENTRYPOINT ["whipper"]
