# -*- Mode: Python -*-
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

import os
import urlparse
import urllib2

from morituri.common import log
from morituri.image import image

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
        if not os.path.exists(path):
            self.debug("%s does not exist, downloading", path)
            self.download(url)

        if not os.path.exists(path):
            self.debug("%s does not exist, not in database", path)
            return None

        data = self._read(url)

        return image.getAccurateRipResponses(data)

    def download(self, url):
        # FIXME: download url as a task too
        responses = []
        import urllib2
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
        os.makedirs(os.path.dirname(path))
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
        
