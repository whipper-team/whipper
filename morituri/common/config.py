# -*- Mode: Python; test-case-name: morituri.test.test_common_config -*-
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

import os.path
import shutil
import urllib
import codecs
import tempfile
import ConfigParser

from morituri.common import log


class Config(log.Loggable):

    def __init__(self, path=None):
        if not path:
            path = self.getDefaultPath()

        self._path = path

        self._parser = ConfigParser.SafeConfigParser()

        self.open()

    def getDefaultPath(self):
        try:
            from xdg import BaseDirectory
            directory = os.path.join(BaseDirectory.xdg_config_home, 'morituri')
            if not os.path.isdir(directory):
                os.mkdir(directory)
            path = os.path.join(directory, 'morituri.conf')
            self.info('Using XDG, configuration file is %s' % path)
            return path
        except ImportError:
            path = os.path.expanduser('~/.moriturirc')
            self.info('Not using XDG, configuration file is %s' % path)
            return path

    def open(self):
        # Open the file with the correct encoding
        if os.path.exists(self._path):
            with codecs.open(self._path, 'r', encoding='utf-8') as f:
                self._parser.readfp(f)

        self.info('Loaded %d sections from config file' %
            len(self._parser.sections()))


    def setReadOffset(self, vendor, model, release, offset):
        """
        Set a read offset for the given drive.

        Strips the given strings of leading and trailing whitespace.
        """
        try:
            section = self._findDriveSection(vendor, model, release)
        except KeyError:
            section = 'drive:' + urllib.quote('%s:%s:%s' % (vendor, model, release))
            self._parser.add_section(section)
            __pychecker__ = 'no-local'
            read_offset = str(offset)
            for key in ['vendor', 'model', 'release', 'read_offset']:
                self._parser.set(section, key, locals()[key].strip())

        self.write()

    def getReadOffset(self, vendor, model, release):
        """
        Get a read offset for the given drive.
        """
        section = self._findDriveSection(vendor, model, release)

        return int(self._parser.get(section, 'read_offset'))

    def _findDriveSection(self, vendor, model, release):
        for name in self._parser.sections():
            if not name.startswith('drive:'):
                continue

            self.debug('Looking at section %r' % name)
            conf = {}
            for key in ['vendor', 'model', 'release']:
                locals()[key] = locals()[key].strip()
                conf[key] = self._parser.get(name, key)
                self.debug("%s: '%s' versus '%s'" % (
                    key, locals()[key], conf[key]))
            if vendor.strip() != conf['vendor']:
                continue
            if model != conf['model']:
                continue
            if release != conf['release']:
                continue

            return name

        raise KeyError

    def write(self):
        fd, path = tempfile.mkstemp(suffix=u'.moriturirc')
        handle = os.fdopen(fd, 'w')
        self._parser.write(handle)
        handle.close()
        shutil.move(path, self._path)
