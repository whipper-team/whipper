# -*- Mode: Python; test-case-name: whipper.test.test_image_cue -*-
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

"""Reading .cue files.

.. seealso:: http://digitalx.org/cuesheetsyntax.php
"""

import re
import codecs

from whipper.common import common
from whipper.image import table

import logging
logger = logging.getLogger(__name__)

_REM_RE = re.compile("^REM\s(\w+)\s(.*)$")
_PERFORMER_RE = re.compile("^PERFORMER\s(.*)$")
_TITLE_RE = re.compile("^TITLE\s(.*)$")

_FILE_RE = re.compile(r"""
    ^FILE                 # FILE
    \s+"(?P<name>.*)"     # 'file name' in quotes
    \s+(?P<format>\w+)$   # format (WAVE/MP3/AIFF/...)
""", re.VERBOSE)

_TRACK_RE = re.compile(r"""
    ^\s+TRACK            # TRACK
    \s+(?P<track>\d\d)   # two-digit track number
    \s+(?P<mode>.+)$    # mode (AUDIO, MODEx/2xxx, ...)
""", re.VERBOSE)

_INDEX_RE = re.compile(r"""
    ^\s+INDEX   # INDEX
    \s+(\d\d)   # two-digit index number
    \s+(\d\d)   # minutes
    :(\d\d)     # seconds
    :(\d\d)$    # frames
""", re.VERBOSE)


class CueFile(object):
    """I represent a .cue file as an object.

    :cvar logCategory:
    :vartype logCategory:
    :ivar path:
    :vartype path:
    :ivar rems:
    :vartype rems:
    :ivar messages:
    :vartype messages:
    :ivar leadout:
    :vartype leadout:
    :ivar table: the index table.
    :vartype table: L{table.Table}
    """

    logCategory = 'CueFile'

    def __init__(self, path):
        assert type(path) is unicode, "%r is not unicode" % path

        self._path = path
        self._rems = {}
        self._messages = []
        self.leadout = None
        self.table = table.Table()

    def parse(self):
        state = 'HEADER'
        currentFile = None
        currentTrack = None
        counter = 0

        logger.info('Parsing .cue file %r', self._path)
        handle = codecs.open(self._path, 'r', 'utf-8')

        for number, line in enumerate(handle.readlines()):
            line = line.rstrip()

            m = _REM_RE.search(line)
            if m:
                tag = m.expand('\\1')
                value = m.expand('\\2')
                if state != 'HEADER':
                    self.message(number, 'REM %s outside of header' % tag)
                else:
                    self._rems[tag] = value
                continue

            # look for FILE lines
            m = _FILE_RE.search(line)
            if m:
                counter += 1
                filePath = m.group('name')
                fileFormat = m.group('format')
                currentFile = File(filePath, fileFormat)

            # look for TRACK lines
            m = _TRACK_RE.search(line)
            if m:
                if not currentFile:
                    self.message(number, 'TRACK without preceding FILE')
                    continue

                state = 'TRACK'

                trackNumber = int(m.group('track'))

                logger.debug('found track %d', trackNumber)
                currentTrack = table.Track(trackNumber)
                self.table.tracks.append(currentTrack)
                continue

            # look for INDEX lines
            m = _INDEX_RE.search(line)
            if m:
                if not currentTrack:
                    self.message(number, 'INDEX without preceding TRACK')
                    print 'ouch'
                    continue

                indexNumber = int(m.expand('\\1'))
                minutes = int(m.expand('\\2'))
                seconds = int(m.expand('\\3'))
                frames = int(m.expand('\\4'))
                frameOffset = frames \
                    + seconds * common.FRAMES_PER_SECOND \
                    + minutes * common.FRAMES_PER_SECOND * 60

                logger.debug('found index %d of track %r in %r:%d',
                             indexNumber, currentTrack, currentFile.path,
                             frameOffset)
                # FIXME: what do we do about File's FORMAT ?
                currentTrack.index(indexNumber,
                                   path=currentFile.path, relative=frameOffset,
                                   counter=counter)
                continue

    def message(self, number, message):
        """Add a message about a given line in the cue file.

        :param number: line number, counting from 0.
        :type number:
        :param message:
        :type message:
        """
        self._messages.append((number + 1, message))

    def getTrackLength(self, track):
        # returns track length in frames, or -1 if can't be determined and
        # complete file should be assumed
        # FIXME: this assumes a track can only be in one file; is this true ?
        i = self.table.tracks.index(track)
        if i == len(self.table.tracks) - 1:
            # last track, so no length known
            return -1

        thisIndex = track.indexes[1]  # FIXME: could be more
        nextIndex = self.table.tracks[i + 1].indexes[1]  # FIXME: could be 0

        c = thisIndex.counter
        if c is not None and c == nextIndex.counter:
            # they belong to the same source, so their relative delta is length
            return nextIndex.relative - thisIndex.relative

        # FIXME: more logic
        return -1

    def getRealPath(self, path):
        """Translate the .cue's FILE to an existing path.

        :param path:
        :type path: unicode
        """
        return common.getRealPath(self._path, path)


class File:
    """I represent a FILE line in a cue file.

    :ivar path:
    :vartype path:
    :ivar format:
    :vartype format:
    """

    def __init__(self, path, format):
        assert type(path) is unicode, "%r is not unicode" % path

        self.path = path
        self.format = format

    def __repr__(self):
        return '<File %r of format %s>' % (self.path, self.format)
