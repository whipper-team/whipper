# -*- Mode: Python; test-case-name: morituri.test.test_common_drive -*-
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

from morituri.common import log


def _listify(listOrString):
    if type(listOrString) == str:
        return [listOrString, ]

    return listOrString


def getAllDevicePaths():
    try:
        return _getAllDevicePathsPyCdio()
    except ImportError:
        log.info('drive', 'Cannot import pycdio')
        return _getAllDevicePathsStatic()


def _getAllDevicePathsPyCdio():
    import pycdio
    import cdio

    # using FS_AUDIO here only makes it list the drive when an audio cd
    # is inserted
    # ticket 102: this cdio call returns a list of str, or a single str
    return _listify(cdio.get_devices_with_cap(pycdio.FS_MATCH_ALL, False))


def _getAllDevicePathsStatic():
    ret = []

    for c in ['/dev/cdrom', '/dev/cdrecorder']:
        if os.path.exists(c):
            ret.append(c)

    return ret
