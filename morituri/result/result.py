# -*- Mode: Python; test-case-name: morituri.test.test_result_result -*-
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

import time

from morituri.result import logger


class TrackResult:
    """
    @type filename:          unicode
    @ivar testcrc:           4-byte CRC for the test read
    @type testcrc:           int
    @ivar copycrc:           4-byte CRC for the copy read
    @type copycrc:           int

    @var  accurip:           whether this track's AR CRC was found in the
                             database, and thus whether the track is considered
                             accurately ripped.
                             If false, it can be ripped wrong, not exist in
                             the database, ...
    @type accurip:           bool

    @var  ARCRC:             our calculated 4 byte AccurateRip CRC for this
                             track.
    @type ARCRC:             int

    @var  ARDBCRC:           the 4-byte AccurateRip CRC this
                             track did or should have matched in the database.
                             If None, the track is not in the database.
    @type ARDBCRC:           int
    @var  ARDBConfidence:    confidence for the matched AccurateRip CRC for
                             this track in the database.
                             If None, the track is not in the database.
    @var  ARDBMaxConfidence: maximum confidence in the AccurateRip database for
                             this track; can still be 0.
                             If None, the track is not in the database.
    """
    number = None
    filename = None
    pregap = 0 # in frames

    peak = 0.0
    quality = 0.0
    testcrc = None
    copycrc = None
    accurip = False # whether it's in the database
    ARCRC = None
    ARDBCRC = None
    ARDBConfidence = None
    ARDBMaxConfidence = None

    classVersion = 2


class RipResult:
    """
    I hold information about the result for rips.
    I can be used to write log files.

    @ivar offset: sample read offset
    @ivar table:  the full index table
    @type table:  L{morituri.image.table.Table}
    """

    offset = 0
    table = None
    artist = None
    title = None

    vendor = None
    model = None

    def __init__(self):
        self.tracks = []

    def getTrackResult(self, number):
        """
        @param number: the track number (0 for HTOA)

        @type  number: int
        @rtype: L{TrackResult}
        """
        for t in self.tracks:
            if t.number == number:
                return t

        return None


class Logger(object):
    """
    I log the result of a rip.
    """

    def log(self, ripResult, epoch=time.time()):
        """
        Create a log from the given ripresult.

        @param epoch:     when the log file gets generated
        @type  ripResult: L{RipResult}

        @rtype: str
        """
        raise NotImplementedError


def getLogger():
    return logger.MorituriLogger()
