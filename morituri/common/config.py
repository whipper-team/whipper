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

from morituri.common import directory, log


class Config(log.Loggable):

    def __init__(self, path=None):
        self._path = path or directory.config_path()

        self._parser = ConfigParser.SafeConfigParser()

        self.open()

    def open(self):
        # Open the file with the correct encoding
        if os.path.exists(self._path):
            with codecs.open(self._path, 'r', encoding='utf-8') as f:
                self._parser.readfp(f)

        self.info('Loaded %d sections from config file' %
            len(self._parser.sections()))

    def write(self):
        fd, path = tempfile.mkstemp(suffix=u'.moriturirc')
        handle = os.fdopen(fd, 'w')
        self._parser.write(handle)
        handle.close()
        shutil.move(path, self._path)


    ### any section

    def _getter(self, suffix, section, option):
        methodName = 'get' + suffix
        method = getattr(self._parser, methodName)
        try:
            return method(section, option)
        except (ConfigParser.NoSectionError, ConfigParser.NoOptionError):
            return None

    def get(self, section, option):
        return self._getter('', section, option)

    def getboolean(self, section, option):
        return self._getter('boolean', section, option)

    ### drive sections

    def setReadOffset(self, vendor, model, release, offset):
        """
        Set a read offset for the given drive.

        Strips the given strings of leading and trailing whitespace.
        """
        section = self._findOrCreateDriveSection(vendor, model, release)
        self._parser.set(section, 'read_offset', str(offset))
        self.write()

    def getReadOffset(self, vendor, model, release):
        """
        Get a read offset for the given drive.
        """
        section = self._findDriveSection(vendor, model, release)

        try:
            return int(self._parser.get(section, 'read_offset'))
        except ConfigParser.NoOptionError:
            raise KeyError("Could not find read_offset for %s/%s/%s" % (
                vendor, model, release))


    def setDefeatsCache(self, vendor, model, release, defeat):
        """
        Set whether the drive defeats the cache.

        Strips the given strings of leading and trailing whitespace.
        """
        section = self._findOrCreateDriveSection(vendor, model, release)
        self._parser.set(section, 'defeats_cache', str(defeat))
        self.write()

    def getDefeatsCache(self, vendor, model, release):
        section = self._findDriveSection(vendor, model, release)

        try:
            return bool(self._parser.get(section, 'defeats_cache'))
        except ConfigParser.NoOptionError:
            raise KeyError("Could not find defeats_cache for %s/%s/%s" % (
                vendor, model, release))

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
            if model.strip() != conf['model']:
                continue
            if release.strip() != conf['release']:
                continue

            return name

        raise KeyError("Could not find configuration section for %s/%s/%s" % (
                vendor, model, release))

    def _findOrCreateDriveSection(self, vendor, model, release):
        try:
            section = self._findDriveSection(vendor, model, release)
        except KeyError:
            section = 'drive:' + urllib.quote('%s:%s:%s' % (
                vendor, model, release))
            self._parser.add_section(section)
            __pychecker__ = 'no-local'
            for key in ['vendor', 'model', 'release']:
                self._parser.set(section, key, locals()[key].strip())

        self.write()

        return self._findDriveSection(vendor, model, release)


