FROM debian:stretch

RUN apt-get update
RUN apt-get install -y cdparanoia cdrdao python-gobject-2 python-musicbrainzngs python-mutagen python-setuptools \
  python-cddb python-requests libsndfile1-dev flac sox \
  libiso9660-dev python-pip swig make pkgconf \
  libcdio-dev libiso9660-dev

RUN pip install pycdio==0.21 --user

RUN mkdir /whipper
COPY . /whipper/
# size matters
RUN cd /whipper && rm -f CHANGELOG.md COVERAGE Dockerfile HACKING LICENSE README* TODO

RUN cd /whipper/src && make && make install && cd ..
RUN cd /whipper && python2 /whipper/setup.py install

WORKDIR /output

ENTRYPOINT ["whipper"]
