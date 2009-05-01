# -*- Mode: Python; test-case-name: morituri.test.test_image_toc -*-
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
Reading .toc files
"""

import os
import re

# header
_CATALOG_RE = re.compile(r'^CATALOG "(?P<catalog>\d+)"$')

# records
_TRACK_RE = re.compile(r"""
    ^TRACK            # TRACK
    \s(?P<mode>.+)$   # mode (AUDIO, MODEx/2xxx, ...)
""", re.VERBOSE)

# a HTOA is marked in the cdrdao's TOC as SILENCE
_SILENCE_RE = re.compile(r"""
    ^SILENCE              # SILENCE
    \s(?P<length>.*)$     # pre-gap length
""", re.VERBOSE)


_FILE_RE = re.compile(r"""
    ^FILE                 # FILE
    \s+"(?P<name>.*)"     # 'file name' in quotes
    \s+(?P<start>.+)      # start offset
    \s(?P<length>.+)$     # stop offset
""", re.VERBOSE)

# FIXME: start can be 0
_START_RE = re.compile(r"""
    ^START                # START
    \s(?P<length>.*)$     # pre-gap length
""", re.VERBOSE)


_INDEX_RE = re.compile(r"""
    ^INDEX            # INDEX
    \s(?P<offset>.+)$ # start offset
""", re.VERBOSE)

class TOC:
    def __init__(self, path):
        self._path = path
        self._messages = []
        self.tracks = []

    def parse(self):
        state = 'HEADER'
        currentFile = None
        currentTrack = None
        trackNumber = 0
        indexNumber = 0
        currentOffset = 0 # running absolute offset of where each track starts
        currentLength = 0 # accrued during TRACK record parsing, current track
        pregapLength = 0 # length of the pre-gap, current track


        # the first track's INDEX 1 can only be gotten from the .toc
        # file once the first pregap is calculated; so we add INDEX 1
        # at the end of each parsed  TRACK record
        handle = open(self._path, 'r')

        for number, line in enumerate(handle.readlines()):
            line = line.rstrip()

            m = _CATALOG_RE.search(line)
            if m:
                catalog = m.group('catalog')

            # look for TRACK lines
            m = _TRACK_RE.search(line)
            if m:
                state = 'TRACK'

                # handle index 1 of previous track, if any
                if currentTrack:
                    currentTrack.index(1, currentOffset + pregapLength,
                        currentFile)

                trackNumber += 1
                currentOffset += currentLength
                currentLength = 0
                indexNumber = 1
                trackMode = m.group('mode')

                currentTrack = Track(trackNumber)
                self.tracks.append(currentTrack)
                continue

            # look for SILENCE lines
            m = _SILENCE_RE.search(line)
            if m:
                length = m.group('length')
                currentLength += self._parseMSF(length)

            # look for FILE lines
            m = _FILE_RE.search(line)
            if m:
                filePath = m.group('name')
                start = m.group('start')
                length = m.group('length')
                currentFile = File(filePath, start, length)
                #currentOffset += self._parseMSF(start)
                currentLength += self._parseMSF(length)

            # look for START lines
            m = _START_RE.search(line)
            if m:
                if not currentTrack:
                    self.message(number, 'START without preceding TRACK')
                    print 'ouch'
                    continue

                length = self._parseMSF(m.group('length'))
                currentTrack.index(0, currentOffset, currentFile)
                currentLength += length
                pregapLength = length
                
             # look for INDEX lines
            m = _INDEX_RE.search(line)
            if m:
                if not currentTrack:
                    self.message(number, 'INDEX without preceding TRACK')
                    indexNumber += 1
                    offset = self._parseMSF(m.group('offset'))
                    currentTrack.index(indexNumber, offset, currentFile)

        # handle index 1 of final track, if any
        if currentTrack:
            currentTrack.index(1, currentOffset + pregapLength, currentFile)

    def message(self, number, message):
        """
        Add a message about a given line in the cue file.

        @param number: line number, counting from 0.
        """
        self._messages.append((number + 1, message))

    def getTrackLength(self, track):
        # returns track length in frames, or -1 if can't be determined and
        # complete file should be assumed
        # FIXME: this assumes a track can only be in one file; is this true ?
        i = self.tracks.index(track)
        if i == len(self.tracks) - 1:
            # last track, so no length known
            return -1

        thisIndex = track._indexes[1] # FIXME: could be more
        nextIndex = self.tracks[i + 1]._indexes[1] # FIXME: could be 0

        if thisIndex[1] == nextIndex[1]: # same file
            return nextIndex[0] - thisIndex[0]

        # FIXME: more logic
        return -1

    def getRealPath(self, path):
        """
        Translate the .cue's FILE to an existing path.
        """
        if os.path.exists(path):
            return path

        # .cue FILE statements have Windows-style path separators, so convert
        tpath = os.path.join(*path.split('\\'))
        candidatePaths = []

        # if the path is relative:
        # - check relatively to the cue file
        # - check only the filename part relative to the cue file
        if tpath == os.path.abspath(tpath):
            candidatePaths.append(tPath)
        else:
            candidatePaths.append(os.path.join(
                os.path.dirname(self._path), tpath))
            candidatePaths.append(os.path.join(
                os.path.dirname(self._path), os.path.basename(tpath)))

        for candidate in candidatePaths:
            noext, _ = os.path.splitext(candidate)
            for ext in ['wav', 'flac']:
                cpath = '%s.%s' % (noext, ext)
                if os.path.exists(cpath):
                    return cpath

        raise KeyError, "Cannot find file for %s" % path

    def _parseMSF(self, msf):
        # parse str value in MM:SS:FF to frames
        if not ':' in msf:
            return int(msf)
        m, s, f = msf.split(':')
        return 60 * 75 * int(m) + 75 * int(s) + int(f)

class File:
    """
    I represent a FILE line in a .toc file.
    """
    def __init__(self, path, start, length):
        self.path = path
        self.start = start
        self.length = length

    def __repr__(self):
        return '<File "%s">' % (self.path, )


# FIXME: add type ? separate AUDIO from others
class Track:
    """
    I represent a track in a cue file.
    I have index points.
    Each index point is linked to an audio file.

    @ivar number: track number
    @type number: int
    """

    def __init__(self, number):
        if number < 1 or number > 99:
            raise IndexError, "Track number must be from 1 to 99"

        self.number = number
        self._indexes = {} # index number -> (sector, File)

        self.title = None
        self.performer = None

    def __repr__(self):
        return '<Track %02d with %d indexes>' % (self.number,
            len(self._indexes.keys()))

    def index(self, number, sector, file):
        """
        Add the given index to the current track.

        @type file: L{File}
        """
        if number in self._indexes.keys():
            raise KeyError, "index %d already in track %d" % (
                number, self.number)
        if number < 0 or number > 99:
            raise IndexError, "Index number must be from 0 to 99"

        self._indexes[number] = (sector, file)

    def getIndex(self, number):
        """
        @rtype: tuple of (int, File)
        """
        return self._indexes[number]
