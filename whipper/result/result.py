# -*- Mode: Python; test-case-name: whipper.test.test_result_result -*-
# vi:si:et:sw=4:sts=4:ts=4

# Copyright (C) 2009 Thomas Vander Stichele

# This file is part of whipper.
#
# whipper is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# whipper is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with whipper.  If not, see <http://www.gnu.org/licenses/>.

import pkg_resources
import time


class TrackResult:
    number = None
    filename = None
    pregap = 0  # in frames
    pre_emphasis = None
    peak = 0
    quality = 0.0
    testspeed = 0.0
    copyspeed = 0.0
    testduration = 0.0
    copyduration = 0.0
    # 4 byte CRCs for the test and copy reads
    testcrc = None
    copycrc = None
    AR = None
    classVersion = 3

    def __init__(self):
        """
        Init TrackResult.

        * CRC: calculated 4 byte AccurateRip CRC
        * DBCRC: 4 byte AccurateRip CRC from the AR database
        * DBConfidence: confidence for the matched AccurateRip DB CRC
        * DBMaxConfidence: track's maximum confidence in the AccurateRip DB
        * DBMaxConfidenceCRC: maximum confidence CRC
        """
        self.AR = {
            'v1': {
                'CRC': None,
                'DBCRC': None,
                'DBConfidence': None,
            },
            'v2': {
                'CRC': None,
                'DBCRC': None,
                'DBConfidence': None,
            },
            'DBMaxConfidence': None,
            'DBMaxConfidenceCRC': None,
        }


class RipResult:
    """
    Hold information about the result for rips.

    It can be used to write log files.

    :cvar offset: sample read offset
    :cvar table: the full index table
    :vartype table: whipper.image.table.Table
    :cvar metadata: disc metadata from MusicBrainz (if available)
    :vartype metadata: whipper.common.mbngs.DiscMetadata
    :cvar vendor: vendor of the CD drive
    :cvar model: model of the CD drive
    :cvar release: release of the CD drive
    :cvar cdrdaoVersion: version of cdrdao used for the rip
    :cvar cdparanoiaVersion: version of cdparanoia used for the rip
    """

    offset = 0
    overread = None
    isCdr = None
    logger = None
    table = None
    artist = None
    title = None
    metadata = None

    vendor = None
    model = None
    release = None

    cdrdaoVersion = None
    cdparanoiaVersion = None
    cdparanoiaDefeatsCache = None

    classVersion = 3

    def __init__(self):
        self.tracks = []

    def getTrackResult(self, number):
        """
        Return TrackResult for the given track number.

        :param number: the track number (0 for HTOA)
        :type number: int
        :returns: TrackResult for the given track number
        :rtype: TrackResult
        """
        for t in self.tracks:
            if t.number == number:
                return t

        return None


class Logger:
    """Log the result of a rip."""

    def log(self, ripResult, epoch=time.time()):
        """
        Create a log from the given ripresult.

        :param epoch: when the log file gets generated
        :type epoch: float
        :type ripResult: RipResult
        :rtype: str
        """
        raise NotImplementedError


# A setuptools-like entry point


class EntryPoint:
    name = 'whipper'

    @staticmethod
    def load():
        from whipper.result import logger
        return logger.WhipperLogger


def getLoggers():
    """
    Get all logger plugins with entry point ``whipper.logger``.

    :rtype: dict(str, Logger)
    """
    d = {}

    pluggables = list(pkg_resources.iter_entry_points("whipper.logger"))
    for entrypoint in [EntryPoint(), ] + pluggables:
        plugin_class = entrypoint.load()
        d[entrypoint.name] = plugin_class

    return d
