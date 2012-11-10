# -*- Mode: Python; test-case-name: morituri.test.test_common_accurip -*-
# vi:si:et:sw=4:sts=4:ts=4

# Morituri - for those about to RIP

# Copyright (C) 2009 Thomas Vander Stichele

# This file is part of morituri.
#
# morituri is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# morituri is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with morituri.  If not, see <http://www.gnu.org/licenses/>.

import errno
import os
import struct
import urlparse
import urllib2

from morituri.common import log

_CACHE_DIR = os.path.join(os.path.expanduser('~'), '.morituri', 'cache')


class AccuCache(log.Loggable):

    def __init__(self):
        if not os.path.exists(_CACHE_DIR):
            self.debug('Creating cache directory %s', _CACHE_DIR)
            os.makedirs(_CACHE_DIR)

    def _getPath(self, url):
        # split path starts with /
        return os.path.join(_CACHE_DIR, urlparse.urlparse(url)[2][1:])

    def retrieve(self, url, force=False):
        self.debug("Retrieving AccurateRip URL %s", url)
        path = self._getPath(url)
        self.debug("Cached path: %s", path)
        if force:
            self.debug("forced to download")
            self.download(url)
        elif not os.path.exists(path):
            self.debug("%s does not exist, downloading", path)
            self.download(url)

        if not os.path.exists(path):
            self.debug("%s does not exist, not in database", path)
            return None

        data = self._read(url)

        return getAccurateRipResponses(data)

    def download(self, url):
        # FIXME: download url as a task too
        try:
            handle = urllib2.urlopen(url)
            data = handle.read()

        except urllib2.HTTPError, e:
            if e.code == 404:
                return None
            else:
                raise

        self._cache(url, data)
        return data

    def _cache(self, url, data):
        path = self._getPath(url)
        try:
            os.makedirs(os.path.dirname(path))
        except OSError, e:
            self.debug('Could not make dir %s: %r' % (
                path, log.getExceptionMessage(e)))
            if e.errno != errno.EEXIST:
                raise

        handle = open(path, 'wb')
        handle.write(data)
        handle.close()

    def _read(self, url):
        self.debug("Reading %s from cache", url)
        path = self._getPath(url)
        handle = open(path, 'rb')
        data = handle.read()
        handle.close()
        return data


def getAccurateRipResponses(data):
    ret = []

    while data:
        trackCount = struct.unpack("B", data[0])[0]
        nbytes = 1 + 12 + trackCount * (1 + 8)

        ret.append(AccurateRipResponse(data[:nbytes]))
        data = data[nbytes:]

    return ret


class AccurateRipResponse(object):
    """
    I represent the response of the AccurateRip online database.

    @type checksums: list of str
    """

    trackCount = None
    discId1 = ""
    discId2 = ""
    cddbDiscId = ""
    confidences = None
    checksums = None

    def __init__(self, data):
        self.trackCount = struct.unpack("B", data[0])[0]
        self.discId1 = "%08x" % struct.unpack("<L", data[1:5])[0]
        self.discId2 = "%08x" % struct.unpack("<L", data[5:9])[0]
        self.cddbDiscId = "%08x" % struct.unpack("<L", data[9:13])[0]

        self.confidences = []
        self.checksums = []

        pos = 13
        for _ in range(self.trackCount):
            confidence = struct.unpack("B", data[pos])[0]
            checksum = "%08x" % struct.unpack("<L", data[pos + 1:pos + 5])[0]
            pos += 9
            self.confidences.append(confidence)
            self.checksums.append(checksum)
