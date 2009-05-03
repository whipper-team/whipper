# -*- Mode: Python; test-case-name: morituri.test.test_image_table -*-
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

"""
Wrap Table of Contents.
"""

import os
import struct

import gst

from morituri.common import task, checksum
from morituri.image import cue

class Track:
    """
    I represent a track entry in a Table of Contents.

    @ivar number: track number (1-based)
    @type number: int
    @ivar start:  start of track, in CD frames (0-based)
    @type start:  int
    @ivar end:    end of track, in CD frames (0-based)
    @type end:    int
    @ivar audio:  whether the track is audio
    @type audio:  bool
    """

    number = None
    start = None
    end = None
    audio = True

    def __repr__(self):
        return '<Track %02d>' % self.number

    def __init__(self, number, start, end, audio=True):
        self.number = number
        self.start = start
        self.end = end
        self.audio = audio

class Table:
    """
    I represent the Table of Contents of a CD.

    @ivar tracks: tracks on this CD
    @type tracks: list of L{Track}
    """

    tracks = None # list of Track

    def __init__(self, tracks=None):
        if not tracks:
            tracks = []

        self.tracks = tracks

    def getTrackStart(self, number):
        """
        @param number: the track number, 1-based
        @type  number: int

        @returns: the start of the given track number, in CD frames
        @rtype:   int
        """
        return self.tracks[number - 1].start

    def getTrackEnd(self, number):
        """
        @param number: the track number, 1-based
        @type  number: int

        @returns: the end of the given track number, in CD frames
        @rtype:   int
        """
        return self.tracks[number - 1].end

    def getTrackLength(self, number):
        """
        @param number: the track number, 1-based
        @type  number: int

        @returns: the length of the given track number, in CD frames
        @rtype:   int
        """
        track = self.tracks[number - 1]
        return track.end - track.start + 1

    def getAudioTracks(self):
        """
        @returns: the number of audio tracks on the CD
        @rtype:   int
        """
        return len([t for t in self.tracks if t.audio])

    def _cddbSum(self, i):
        ret = 0
        while i > 0:
            ret += (i % 10)
            i /= 10

        return ret

    def getCDDBDiscId(self):
        """
        Calculate the CDDB disc ID.

        @rtype:   str
        @returns: the 8-character hexadecimal disc ID
        """
        # cddb disc id takes into account data tracks
        # last byte is the number of tracks on the CD
        n = 0

        for track in self.tracks:
            # CD's have a standard lead-in time of 2 seconds
            # which gets added for CDDB disc id's
            offset = self.getTrackStart(track.number) + \
                2 * checksum.FRAMES_PER_SECOND
            seconds = offset / checksum.FRAMES_PER_SECOND
            n += self._cddbSum(seconds)

        last = self.tracks[-1]
        leadout = self.getTrackEnd(last.number)
        frameLength = leadout - self.getTrackStart(1)
        t = frameLength / checksum.FRAMES_PER_SECOND

        value = (n % 0xff) << 24 | t << 8 | len(self.tracks)
        
        return "%08x" % value

    def getAccurateRipIds(self):
        """
        Calculate the two AccurateRip ID's.

        @returns: the two 8-character hexadecimal disc ID's
        @rtype:   tuple of (str, str)
        """
        # AccurateRip does not take into account data tracks,
        # but does count the data track to determine the leadout offset
        discId1 = 0
        discId2 = 0

        for track in self.tracks:
            if not track.audio:
                continue
            offset = self.getTrackStart(track.number)
            discId1 += offset
            discId2 += (offset or 1) * track.number

        # also add end values, where leadout offset is one past the end
        # of the last track
        last = self.tracks[-1]
        offset = self.getTrackEnd(last.number) + 1
        discId1 += offset
        discId2 += offset * (self.getAudioTracks() + 1)

        discId1 &= 0xffffffff
        discId2 &= 0xffffffff

        return ("%08x" % discId1, "%08x" % discId2)

    def getAccurateRipURL(self):
        """
        Return the full AccurateRip URL.

        @returns: the AccurateRip URL
        @rtype:   str
        """
        discId1, discId2 = self.getAccurateRipIds()

        return "http://www.accuraterip.com/accuraterip/" \
            "%s/%s/%s/dBAR-%.3d-%s-%s-%s.bin" % ( 
                discId1[-1], discId1[-2], discId1[-3],
                len(self.tracks), discId1, discId2, self.getCDDBDiscId())
