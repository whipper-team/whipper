# -*- Mode: Python; test-case-name: morituri.test.test_common_directory -*-
# vi:si:et:sw=4:sts=4:ts=4

# Morituri - for those about to RIP

# Copyright (C) 2013 Thomas Vander Stichele

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

from morituri.common import log


class Directory(log.Loggable):

    def getConfig(self):
        config_directory = os.getenv('XDG_CONFIG_HOME')
        if not config_directory:
            config_directory = os.path.join(os.path.expanduser('~'),
                                            u'.config')
        folder_path = os.path.join(config_directory, u'whipper')
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
        path = os.path.join(config_directory, u'whipper/whipper.conf')
        self.info('Configuration file path: %s' % path)
        return path

    def getCache(self, name=None):
        cache_directory = os.getenv('XDG_CACHE_HOME')
        if not cache_directory:
            cache_directory = os.path.join(os.path.expanduser('~'), u'.cache')
        path = os.path.join(cache_directory, u'whipper')
        self.info('Cache directory path: %s' % path)
        if not os.path.exists(path):
            os.makedirs(path)
        if name:
            path = os.path.join(path, name)
            if not os.path.exists(path):
                os.makedirs(path)
        return path

    def getData(self, name=None):
        data_directory = os.getenv('XDG_DATA_HOME')
        if not data_directory:
            data_directory = os.path.join(os.path.expanduser('~'),
                                          u'.local/share')
        path = os.path.join(data_directory, u'whipper')
        self.info('Data directory path: %s' % path)
        if not os.path.exists(path):
            os.makedirs(path)
        if name:
            path = os.path.join(path, name)
            if not os.path.exists(path):
                os.makedirs(path)
        return path

