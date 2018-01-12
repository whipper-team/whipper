# -*- Mode: Python; test-case-name: whipper.test.test_image_toc -*-
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

"""Reading .toc files.

The .toc file format is described in the man page of cdrdao.
"""

import re
import codecs

from whipper.common import common
from whipper.image import table

import logging
logger = logging.getLogger(__name__)

# shared
_CDTEXT_CANDIDATE_RE = re.compile(r'(?P<key>\w+) "(?P<value>.+)"')

# header
_CATALOG_RE = re.compile(r'^CATALOG "(?P<catalog>\d+)"$')

# pre emphasis
_PRE_EMPHASIS_RE = re.compile(r'^PRE_EMPHASIS$')

# records
_TRACK_RE = re.compile(r"""
    ^TRACK            # TRACK
    \s(?P<mode>.+)$   # mode (AUDIO, MODE2_FORM_MIX, MODEx/2xxx, ...)
""", re.VERBOSE)

_ISRC_RE = re.compile(r'^ISRC "(?P<isrc>\w+)"$')

# a HTOA is marked in the cdrdao's TOC as SILENCE
_SILENCE_RE = re.compile(r"""
    ^SILENCE              # SILENCE
    \s(?P<length>.*)$     # pre-gap length
""", re.VERBOSE)

# ZERO is used as pre-gap source when switching mode
_ZERO_RE = re.compile(r"""
    ^ZERO                 # ZERO
    \s(?P<mode>.+)        # mode (AUDIO, MODEx/2xxx, ...)
    \s(?P<length>.*)$     # zero length
""", re.VERBOSE)


_FILE_RE = re.compile(r"""
    ^FILE                 # FILE
    \s+"(?P<name>.*)"     # 'file name' in quotes
    \s+(?P<start>.+)      # start offset
    \s(?P<length>.+)$     # length in frames of section
""", re.VERBOSE)

_DATAFILE_RE = re.compile(r"""
    ^DATAFILE             # DATA FILE
    \s+"(?P<name>.*)"     # 'file name' in quotes
    \s+(?P<length>\S+)    # start offset
    \s*.*                 # possible // comment
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


class Sources:
    """I represent the list of sources used in the .toc file.

    Each SILENCE and each FILE is a source.
    If the filename for FILE doesn't change, the counter is not increased.

    ivar sources:
    vartype sources:
    """

    def __init__(self):
        self._sources = []

    def append(self, counter, offset, source):
        """Append tuple containing source information to sources.

        This method also logs the event.

        :param counter: the source counter; updates for each different
                        data source (silence or different file path).
        :type counter: int
        :param offset: the absolute disc offset where this source starts.
        :type offset:
        :param source:
        :type source:
        """
        logger.debug('Appending source, counter %d, abs offset %d, '
                     'source %r' % (counter, offset, source))
        self._sources.append((counter, offset, source))

    def get(self, offset):
        """Retrieve the source used at the given offset.

        :param offset:
        :type offset:
        """
        for i, (c, o, s) in enumerate(self._sources):
            if offset < o:
                return self._sources[i - 1]

        return self._sources[-1]

    def getCounterStart(self, counter):
        """Retrieve the absolute offset of the first source for this counter.

        :param counter:
        :type counter:
        """
        for i, (c, o, s) in enumerate(self._sources):
            if c == counter:
                return self._sources[i][1]

        return self._sources[-1][1]


class TocFile(object):
    """I represent a .toc file.

    :ivar path:
    :vartype path: unicode
    :ivar messages:
    :vartype messages:
    :ivar table:
    :vartype table:
    :ivar logName:
    :vartype logName:
    :ivar sources:
    :vartype sources:
    """

    def __init__(self, path):
        assert type(path) is unicode, "%r is not unicode" % path
        self._path = path
        self._messages = []
        self.table = table.Table()
        self.logName = '<TocFile %08x>' % id(self)

        self._sources = Sources()

    def _index(self, currentTrack, i, absoluteOffset, trackOffset):
        absolute = absoluteOffset + trackOffset
        # this may be in a new source, so calculate relative
        c, o, s = self._sources.get(absolute)
        logger.debug('at abs offset %d, we are in source %r' % (
            absolute, s))
        counterStart = self._sources.getCounterStart(c)
        relative = absolute - counterStart

        currentTrack.index(i, path=s.path,
                           absolute=absolute,
                           relative=relative,
                           counter=c)
        logger.debug(
            '[track %02d index %02d] trackOffset %r, added %r',
            currentTrack.number, i, trackOffset,
            currentTrack.getIndex(i))

    def parse(self):
        currentFile = None
        currentTrack = None

        state = 'HEADER'
        # counts sources for audio data; SILENCE/ZERO/FILE
        counter = 0
        trackNumber = 0
        indexNumber = 0
        # running absolute offset: where each track starts
        absoluteOffset = 0
        # running relative offset, relative to counter src
        relativeOffset = 0
        # currentLength is accrued during TRACK record parsing length
        # of current track as parsed so far reset on each TRACK statement
        currentLength = 0
        # accrued during TRACK record parsing, total disc
        totalLength = 0
        # length of the pre-gap, current track in for loop
        pregapLength = 0

        # the first track's INDEX 1 can only be gotten from the .toc
        # file once the first pregap is calculated; so we add INDEX 1
        # at the end of each parsed  TRACK record
        handle = codecs.open(self._path, "r", "utf-8")

        for number, line in enumerate(handle.readlines()):
            line = line.rstrip()

            # look for CDTEXT stuff in either header or tracks
            m = _CDTEXT_CANDIDATE_RE.search(line)
            if m:
                key = m.group('key')
                value = m.group('value')
                # usually, value is encoded with octal escapes and in latin-1
                # FIXME: other encodings are possible, does cdrdao handle
                # them ?
                value = value.decode('string-escape').decode('latin-1')
                if key in table.CDTEXT_FIELDS:
                    # FIXME: consider ISRC separate for now, but this
                    # is a limitation of our parser approach
                    if state == 'HEADER':
                        self.table.cdtext[key] = value
                        logger.debug('Found disc CD-Text %s: %r', key, value)
                    elif state == 'TRACK':
                        if key != 'ISRC' or not currentTrack \
                                or currentTrack.isrc is not None:
                            logger.debug('Found track CD-Text %s: %r',
                                         key, value)
                            currentTrack.cdtext[key] = value

            # look for header elements
            m = _CATALOG_RE.search(line)
            if m:
                self.table.catalog = m.group('catalog')
                logger.debug("Found catalog number %s", self.table.catalog)

            # look for TRACK lines
            m = _TRACK_RE.search(line)
            if m:
                state = 'TRACK'

                # set index 1 of previous track if there was one, using
                # pregapLength if applicable
                if currentTrack:
                    self._index(currentTrack, 1, absoluteOffset, pregapLength)

                # create a new track to be filled by later lines
                trackNumber += 1
                trackMode = m.group('mode')
                audio = trackMode == 'AUDIO'
                currentTrack = table.Track(trackNumber, audio=audio)
                self.table.tracks.append(currentTrack)

                # update running totals
                absoluteOffset += currentLength
                relativeOffset += currentLength
                totalLength += currentLength

                # FIXME: track mode
                logger.debug('found track %d, mode %s, at absoluteOffset %d',
                             trackNumber, trackMode, absoluteOffset)

                # reset counters relative to a track
                currentLength = 0
                indexNumber = 1
                pregapLength = 0

                continue

            # look for PRE_EMPHASIS lines
            m = _PRE_EMPHASIS_RE.search(line)
            if m:
                currentTrack.pre_emphasis = True
                logger.debug('Track has PRE_EMPHASIS')

            # look for ISRC lines
            m = _ISRC_RE.search(line)
            if m:
                isrc = m.group('isrc')
                currentTrack.isrc = isrc
                logger.debug('Found ISRC code %s', isrc)

            # look for SILENCE lines
            m = _SILENCE_RE.search(line)
            if m:
                length = m.group('length')
                logger.debug('SILENCE of %r', length)
                self._sources.append(counter, absoluteOffset, None)
                if currentFile is not None:
                    logger.debug('SILENCE after FILE, increasing counter')
                    counter += 1
                    relativeOffset = 0
                    currentFile = None
                currentLength += common.msfToFrames(length)

            # look for ZERO lines
            m = _ZERO_RE.search(line)
            if m:
                if currentFile is not None:
                    logger.debug('ZERO after FILE, increasing counter')
                    counter += 1
                    relativeOffset = 0
                    currentFile = None
                length = m.group('length')
                currentLength += common.msfToFrames(length)

            # look for FILE lines
            m = _FILE_RE.search(line)
            if m:
                filePath = m.group('name')
                start = m.group('start')
                length = m.group('length')
                logger.debug('FILE %s, start %r, length %r',
                             filePath, common.msfToFrames(start),
                             common.msfToFrames(length))
                if not currentFile or filePath != currentFile.path:
                    counter += 1
                    relativeOffset = 0
                    logger.debug('track %d, switched to new FILE, '
                                 'increased counter to %d',
                                 trackNumber, counter)
                currentFile = File(filePath, common.msfToFrames(start),
                                   common.msfToFrames(length))
                self._sources.append(counter, absoluteOffset + currentLength,
                                     currentFile)
                currentLength += common.msfToFrames(length)

            # look for DATAFILE lines
            m = _DATAFILE_RE.search(line)
            if m:
                filePath = m.group('name')
                length = m.group('length')
                logger.debug('FILE %s, length %r',
                             filePath, common.msfToFrames(length))
                if not currentFile or filePath != currentFile.path:
                    counter += 1
                    relativeOffset = 0
                    logger.debug('track %d, switched to new FILE, '
                                 'increased counter to %d',
                                 trackNumber, counter)
                # FIXME: assume that a MODE2_FORM_MIX track always starts at 0
                currentFile = File(filePath, 0, common.msfToFrames(length))
                self._sources.append(counter, absoluteOffset + currentLength,
                                     currentFile)
                currentLength += common.msfToFrames(length)

            # look for START lines
            m = _START_RE.search(line)
            if m:
                if not currentTrack:
                    self.message(number, 'START without preceding TRACK')
                    print 'ouch'
                    continue

                length = common.msfToFrames(m.group('length'))
                c, o, s = self._sources.get(absoluteOffset)
                logger.debug('at abs offset %d, we are in source %r' % (
                    absoluteOffset, s))
                counterStart = self._sources.getCounterStart(c)
                relativeOffset = absoluteOffset - counterStart

                currentTrack.index(0, path=s and s.path or None,
                                   absolute=absoluteOffset,
                                   relative=relativeOffset, counter=c)
                logger.debug('[track %02d index 00] added %r',
                             currentTrack.number, currentTrack.getIndex(0))
                # store the pregapLength to add it when we index 1 for this
                # track on the next iteration
                pregapLength = length

            # look for INDEX lines
            m = _INDEX_RE.search(line)
            if m:
                if not currentTrack:
                    self.message(number, 'INDEX without preceding TRACK')
                    print 'ouch'
                    continue

                indexNumber += 1
                offset = common.msfToFrames(m.group('offset'))
                self._index(currentTrack, indexNumber, absoluteOffset, offset)

        # handle index 1 of final track, if any
        if currentTrack:
            self._index(currentTrack, 1, absoluteOffset, pregapLength)

        # totalLength was added up to the penultimate track
        self.table.leadout = totalLength + currentLength
        logger.debug('parse: leadout: %r', self.table.leadout)

    def message(self, number, message):
        """Add a message about a given line in the cue file.

        :param number: line number, counting from 0.
        :type number:
        :param message:
        :type message:
        """
        self._messages.append((number + 1, message))

    def getTrackLength(self, track):
        """Compute the length of the given track.

        The lenght is computed from its INDEX 01 to the next track's INDEX 01.

        :param track:
        :type track:
        """
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
        """Translate the .toc's FILE to an existing path.

        :param path:
        :type path: unicode
        """
        return common.getRealPath(self._path, path)


class File:
    """I represent a FILE line in a .toc file.

    :ivar path:
    :vartype path: C{unicode}
    :ivar start: starting point for the track in this file, in frames.
    :vartype start: C{int}
    :ivar length: length for the track in this file, in frames.
    :vartype length:
    """

    def __init__(self, path, start, length):
        assert type(path) is unicode, "%r is not unicode" % path

        self.path = path
        self.start = start
        self.length = length

    def __repr__(self):
        return '<File %r>' % (self.path, )
