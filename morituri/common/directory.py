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
        try:
            from xdg import BaseDirectory
            directory = BaseDirectory.save_config_path('morituri')
            path = os.path.join(directory, 'morituri.conf')
            self.info('Using XDG, configuration file is %s' % path)
        except ImportError:
            path = os.path.expanduser('~/.moriturirc')
            self.info('Not using XDG, configuration file is %s' % path)
        return path


    def getCache(self, name=None):
        try:
            from xdg import BaseDirectory
            path = BaseDirectory.save_cache_path('morituri')
            self.info('Using XDG, cache directory is %s' % path)
        except ImportError:
            path = os.path.expanduser('~/.morituri/cache')
            if not os.path.exists(path):
                os.makedirs(path)
            self.info('Not using XDG, cache directory is %s' % path)

        if name:
            path = os.path.join(path, name)
            if not os.path.exists(path):
                os.makedirs(path)

        return path

    def getReadCaches(self, name=None):
        paths = []

        try:
            from xdg import BaseDirectory
            path = BaseDirectory.save_cache_path('morituri')
            self.info('For XDG, read cache directory is %s' % path)
            paths.append(path)
        except ImportError:
            pass

        path = os.path.expanduser('~/.morituri/cache')
        if os.path.exists(path):
            self.info('From before XDG, read cache directory is %s' % path)
            paths.append(path)

        if name:
            paths = [os.path.join(p, name) for p in paths]

        return paths


