# -*- Mode: Python; test-case-name: whipper.test.test_image_table -*-
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

"""Wrap Table of Contents."""

import copy
from urllib.parse import urlunparse, urlencode

import whipper

from whipper.common import common, config
from whipper.extern.freedb import DiscID

import logging
logger = logging.getLogger(__name__)

# FIXME: taken from libcdio, but no reference found for these

CDTEXT_FIELDS = [
    'ARRANGER',
    'COMPOSER',
    'DISCID',
    'GENRE',
    'MESSAGE',
    'ISRC',
    'PERFORMER',
    'SIZE_INFO',
    'SONGWRITER',
    'TITLE',
    'TOC_INFO',
    'TOC_INFO2',
    'UPC_EAN',
]


class Track:
    """
    Represent a track entry in a Table.

    :cvar number: track number (1-based)
    :vartype number: int
    :cvar audio: whether the track is audio
    :vartype audio: bool
    :cvar indexes: dict of number
    :vartype indexes: dict of number -> :any:`Index`
    :cvar isrc: ISRC code (12 alphanumeric characters)
    :vartype isrc: str
    :cvar cdtext: dictionary of CD Text information;
                  :any:`see CDTEXT_KEYS`
    :vartype cdtext: str
    :cvar pre_emphasis: whether track is pre-emphasised
    :vartype pre_emphasis: bool
    """

    number = None
    audio = None
    indexes = None
    isrc = None
    cdtext = None
    session = None
    pre_emphasis = None

    def __repr__(self):
        return '<Track %02d>' % self.number

    def __init__(self, number, audio=True, session=None):
        self.number = number
        self.audio = audio
        self.indexes = {}
        self.cdtext = {}

    def index(self, number, absolute=None, path=None, relative=None,
              counter=None):
        """
        Instantiate Index object and store it in class variable.

        :param number: index number
        :type number: int
        :param absolute: absolute index offset, in CD frames
        :type absolute: int or None
        :param path: path to track
        :type path: str or None
        :param relative: relative index offset, in CD frames
        :type relative: int or None
        :param counter: the source counter; updates for each different
                        data source (silence or different file path)
        :type counter: int or None
        """
        if path is not None:
            assert isinstance(path, str), "%r is not str" % path

        i = Index(number, absolute, path, relative, counter)
        self.indexes[number] = i

    def getIndex(self, number):
        return self.indexes[number]

    def getFirstIndex(self):
        """
        Get the first chronological index for this track.

        Typically this is INDEX 01; but it could be INDEX 00 if there's
        a pre-gap.
        """
        indexes = sorted(self.indexes.keys())
        return self.indexes[indexes[0]]

    def getLastIndex(self):
        indexes = sorted(self.indexes.keys())
        return self.indexes[indexes[-1]]

    def getPregap(self):
        """
        Return the length of the pregap for this track.

        The pregap is 0 if there is no index 0, and the difference between
        index 1 and index 0 if there is.
        """
        if 0 not in self.indexes:
            return 0

        return self.indexes[1].absolute - self.indexes[0].absolute


class Index:
    """
    Represent an index of a track on a CD.

    :cvar counter: counter for the index source; distinguishes between
                   the matching FILE lines in .cue files for example
    :vartype counter: int
    :cvar path: path to track
    :vartype path: str or None
    """

    number = None
    absolute = None
    path = None
    relative = None
    counter = None

    def __init__(self, number, absolute=None, path=None, relative=None,
                 counter=None):

        if path is not None:
            assert isinstance(path, str), "%r is not str" % path

        self.number = number
        self.absolute = absolute
        self.path = path
        self.relative = relative
        self.counter = counter

    def __repr__(self):
        return '<Index %02d absolute %r path %r relative %r counter %r>' % (
            self.number, self.absolute, self.path, self.relative, self.counter)


class Table:
    """
    Represent a table of indexes on a CD.

    :cvar tracks: tracks on this CD
    :vartype tracks: list(Track)
    :cvar catalog: catalog number
    :vartype catalog: str
    """

    tracks = None  # list of Track
    leadout = None  # offset where the leadout starts
    catalog = None  # catalog number; FIXME: is this UPC ?
    cdtext = None
    mbdiscid = None

    classVersion = 4

    def __init__(self, tracks=None):
        if not tracks:
            tracks = []

        self.tracks = tracks
        self.cdtext = {}
        # done this way because just having a class-defined instance var
        # gets overridden when unpickling
        self.instanceVersion = self.classVersion
        self.unpickled()

    def unpickled(self):
        self.logName = "Table 0x%08x v%d" % (id(self), self.instanceVersion)
        logger.debug('set logName')

    def getTrackStart(self, number):
        """
        Return the start of the given track number's index 1, in CD frames.

        :param number: the track number, 1-based
        :type number: int
        :returns: the start of the given track number's index 1, in CD frames
        :rtype: int
        """
        track = self.tracks[number - 1]
        return track.getIndex(1).absolute

    def getTrackEnd(self, number):
        """
        Return the end of the given track number, in CD frames.

        :param number: the track number, 1-based
        :type number: int
        :returns: the end of the given track number (ie index 1 of next track)
        :rtype: int
        """
        # default to end of disc
        end = self.leadout - 1

        # if not last track, calculate it from the next track
        if number < len(self.tracks):
            end = self.tracks[number].getIndex(1).absolute - 1

            # if on a session border, subtract the session leadin
            thisTrack = self.tracks[number - 1]
            nextTrack = self.tracks[number]
            # The session attribute of a track is None by default (session 1)
            # with value > 1 if the track is in another session. Py3 doesn't
            # allow NoneType comparisons so we compare against 1 in that case
            if int(nextTrack.session or 1) > int(thisTrack.session or 1):
                gap = self._getSessionGap(nextTrack.session)
                end -= gap

        return end

    def getTrackLength(self, number):
        """
        Return the length, in CD frames, for the given track number.

        :param number: the track number, 1-based
        :type number: int
        :returns: the length of the given track number, in CD frames
        :rtype: int
        """
        return self.getTrackEnd(number) - self.getTrackStart(number) + 1

    def getAudioTracks(self):
        """
        Return the number of audio tracks on the disc.

        :returns: the number of audio tracks on the disc
        :rtype: int
        """
        return len([t for t in self.tracks if t.audio])

    def hasDataTracks(self):
        """
        Return whether the disc contains data tracks.

        :returns: whether the disc contains data tracks
        :rtype: bool
        """
        return len([t for t in self.tracks if not t.audio]) > 0

    @staticmethod
    def _cddbSum(i):
        ret = 0
        while i > 0:
            ret += (i % 10)
            i /= 10

        return ret

    def getCDDBValues(self):
        """
        Get all CDDB values needed to calculate disc id and lookup URL.

        This includes:

        * CDDB disc id
        * number of audio tracks
        * offset of index 1 of each track
        * length of disc in seconds (including data track)

        :rtype: list(int)
        """
        offsets = []

        # cddb disc id takes into account data tracks
        # last byte is the number of tracks on the CD
        n = 0

        # CD's have a standard lead-in time of 2 seconds
        # which gets added for CDDB disc id's
        delta = 2 * common.FRAMES_PER_SECOND

        debug = [str(len(self.tracks))]
        for track in self.tracks:
            offset = self.getTrackStart(track.number) + delta
            offsets.append(offset)
            debug.append(str(offset))
            seconds = offset // common.FRAMES_PER_SECOND
            n += self._cddbSum(seconds)

        # the 'real' leadout, not offset by 150 frames
        last = self.tracks[-1]
        leadout = self.getTrackEnd(last.number) + 1
        logger.debug('leadout LBA: %d', leadout)

        # FIXME: we can't replace these calculations with the getFrameLength
        # call because the start and leadout in the algorithm get rounded
        # before making the difference
        startSeconds = self.getTrackStart(1) // common.FRAMES_PER_SECOND
        leadoutSeconds = leadout // common.FRAMES_PER_SECOND
        t = leadoutSeconds - startSeconds
        # durationFrames = self.getFrameLength(data=True)
        # duration = durationFrames / common.FRAMES_PER_SECOND
        # assert t == duration, "%r != %r" % (t, duration)

        debug.append(str(leadoutSeconds + 2))  # 2 is the 150 frame cddb offset

        result = DiscID(offsets, t, len(self.tracks), leadoutSeconds)
        value = int(result)

        # compare this debug line to cd-discid output
        logger.debug('cddb values: %r', result)

        logger.debug('cddb disc id debug: %s',
                     " ".join(["%08x" % value, ] + debug))

        return result

    def getCDDBDiscId(self):
        """
        Calculate the CDDB disc ID.

        :returns: the 8-character hexadecimal disc ID
        :rtype: str
        """
        values = self.getCDDBValues()
        return "%08x" % int(values)

    def getMusicBrainzDiscId(self):
        """
        Calculate the MusicBrainz disc ID.

        :returns: the 28-character base64-encoded disc ID
        :rtype: str
        """
        if self.mbdiscid:
            logger.debug('getMusicBrainzDiscId: returning cached %r',
                         self.mbdiscid)
            return self.mbdiscid

        from discid import put

        values = self._getMusicBrainzValues()

        disc = put(values[0], values[1], values[2], values[3:])
        logger.debug('getMusicBrainzDiscId: returning %r', disc.id)
        self.mbdiscid = disc.id
        return disc.id

    def getMusicBrainzSubmitURL(self):
        serv = config.Config().get_musicbrainz_server()

        discid = self.getMusicBrainzDiscId()
        values = self._getMusicBrainzValues()

        query = urlencode([
            ('toc', ' '.join([str(v) for v in values])),
            ('tracks', self.getAudioTracks()),
            ('id', discid),
        ])

        return urlunparse((
            serv['scheme'], serv['netloc'], '/cdtoc/attach', '', query, ''))

    def getFrameLength(self, data=False):
        """
        Get the length in frames (excluding HTOA).

        :param data: whether to include the data tracks in the length
        :type data: bool
        """
        # the 'real' leadout, not offset by 150 frames
        if data:
            last = self.tracks[-1]
        else:
            last = self.tracks[self.getAudioTracks() - 1]

        leadout = self.getTrackEnd(last.number) + 1
        logger.debug('leadout LBA: %d', leadout)
        durationFrames = leadout - self.getTrackStart(1)

        return durationFrames

    def duration(self):
        """Get the duration in ms for all audio tracks (excluding HTOA)."""
        return int(self.getFrameLength() * 1000.0 / common.FRAMES_PER_SECOND)

    def _getMusicBrainzValues(self):
        """
        Get all MusicBrainz values needed to calculate disc id and submit URL.

        This includes:

        * track number of first track
        * number of audio tracks
        * leadout of disc
        * offset of index 1 of each track

        :rtype: list(int)
        """
        # MusicBrainz disc id does not take into account data tracks

        result = []

        # number of first track
        result.append(1)

        # number of last audio track (default: number of audio tracks)
        lastTrack = self.getAudioTracks()
        result.append(lastTrack)

        dataTrackLast = False
        additional = 0
        offsets = []

        # offsets of tracks
        for i in range(0, len(self.tracks)):
            track = self.tracks[i]
            if not track.audio:
                # if the data track is not at the end
                if i < len(self.tracks) - 1:
                    additional += 1
                else:
                    # if the data track is last
                    dataTrackLast = True
                    sectors = self.tracks[-1].getIndex(1).absolute - 11400
                    # treat leadout offset as track 0 offset
                    sectors += 150
                continue
            offset = track.getIndex(1).absolute + 150
            offsets.append(offset)

        if not dataTrackLast:
            # the end of the last audio track, +1 since getTrackEnd returned
            # value is always down by 1 unit. Which means that's actually
            # offsets[-1] + getTrackLength(lastTrack).
            sectors = self.getTrackEnd(lastTrack + additional) + 1 + 150

        result.append(sectors)
        result.extend(offsets)

        logger.debug('MusicBrainz values: %r', result)
        return result

    def cue(self, cuePath='', program='whipper'):
        """
        Dump our internal representation to a .cue file content.

        :param cuePath: path to the cue file to be written. If empty,
                        will treat paths as if in current directory
        :type cuePath: unicode
        :param program: name of the program (ripping software)
        :type program: str
        :rtype: str
        """
        logger.debug('generating .cue for cuePath %r', cuePath)

        lines = []

        def writeFile(path):
            targetPath = common.getRelativePath(path, cuePath)
            line = 'FILE "%s" WAVE' % targetPath
            lines.append(line)
            logger.debug('writeFile: %r', line)

        # header
        main = ['PERFORMER', 'TITLE']

        for key in CDTEXT_FIELDS:
            if key not in main and key in self.cdtext:
                lines.append("    %s %s" % (key, self.cdtext[key]))

        assert self.hasTOC(), "Table does not represent a full CD TOC"
        lines.append('REM DISCID %s' % self.getCDDBDiscId().upper())
        lines.append('REM COMMENT "%s %s"' % (program, whipper.__version__))

        if self.catalog:
            lines.append("CATALOG %s" % self.catalog)

        for key in main:
            if key in self.cdtext:
                lines.append('%s "%s"' % (key, self.cdtext[key]))

        # FIXME:
        # - the first FILE statement goes before the first TRACK, even if
        #   there is a non-file-using PREGAP
        # - the following FILE statements come after the last INDEX that
        #   use that FILE; so before a next TRACK, PREGAP silence, ...

        # add the first FILE line; EAC always puts the first FILE
        # statement before TRACK 01 and any possible PRE-GAP
        firstTrack = self.tracks[0]
        index = firstTrack.getFirstIndex()
        indexOne = firstTrack.getIndex(1)
        counter = index.counter
        track = firstTrack

        while not index.path:
            t, i = self.getNextTrackIndex(track.number, index.number)
            track = self.tracks[t - 1]
            index = track.getIndex(i)
            counter = index.counter

        if index.path:
            logger.debug('counter %d, writeFile', counter)
            writeFile(index.path)

        for i, track in enumerate(self.tracks):
            logger.debug('track i %r, track %r', i, track)
            # FIXME: skip data tracks for now
            if not track.audio:
                continue

            indexes = sorted(track.indexes.keys())

            wroteTrack = False

            for number in indexes:
                index = track.indexes[number]
                logger.debug('index %r, %r', number, index)

                # any time the source counter changes to a higher value,
                # write a FILE statement
                # it has to be higher, because we can run into the HTOA
                # at counter 0 here
                if index.counter > counter:
                    if index.path:
                        logger.debug('counter %d, writeFile', counter)
                        writeFile(index.path)
                    logger.debug('setting counter to index.counter %r',
                                 index.counter)
                    counter = index.counter

                # any time we hit the first index, write a TRACK statement
                if not wroteTrack:
                    wroteTrack = True
                    line = "  TRACK %02d %s" % (i + 1, 'AUDIO')
                    lines.append(line)
                    logger.debug('%r', line)

                    for key in CDTEXT_FIELDS:
                        if key in track.cdtext:
                            lines.append('    %s "%s"' % (
                                key, track.cdtext[key]))

                    if track.isrc is not None:
                        lines.append("    ISRC %s" % track.isrc)

                    if track.pre_emphasis is not None:
                        lines.append("    FLAGS PRE")

                    # handle TRACK 01 INDEX 00 specially
                    if 0 in indexes:
                        index00 = track.indexes[0]
                        if i == 0:
                            # if we have a silent pre-gap, output it
                            if not index00.path:
                                length = indexOne.absolute - index00.absolute
                                lines.append("    PREGAP %s" %
                                             common.framesToMSF(length))
                                continue

                        # handle any other INDEX 00 after its TRACK
                        lines.append("    INDEX "
                                     "%02d %s" % (0, common.framesToMSF(
                                                        index00.relative)))

                if number > 0:
                    # index 00 is output after TRACK up above
                    lines.append("    INDEX %02d %s" % (number,
                                                        common.framesToMSF(
                                                            index.relative)))

        lines.append("")

        return "\n".join(lines)

    # methods that modify the table

    def clearFiles(self):
        """
        Clear all file backings.

        Resets indexes paths and relative offsets.
        """
        # FIXME: do a loop over track indexes better, with a pythonic
        # construct that allows you to do for t, i in ...
        t = self.tracks[0].number
        index = self.tracks[0].getFirstIndex()
        i = index.number

        logger.debug('clearing path')
        while True:
            track = self.tracks[t - 1]
            index = track.getIndex(i)
            logger.debug('clearing path on track %d, index %d', t, i)
            index.path = None
            index.relative = None
            try:
                t, i = self.getNextTrackIndex(t, i)
            except IndexError:
                break

    def setFile(self, track, index, path, length, counter=None):
        """
        Set the given file as the source from the given index on.

        Will loop over all indexes that fall within the given length,
        to adjust the path.

        Assumes all indexes have an absolute offset and will raise if not.

        :param track: track number, 1-based
        :type track: int
        :param index: index of the track
        :type index: int
        :param path: path to track
        :type path: unicode
        :param length: length of the given track, in CD frames
        :type length: int
        :param counter: counter for the index source; distinguishes between
                        the matching FILE lines in .cue files for example
        :type counter: int or None
        """
        logger.debug('setFile: track %d, index %d, path %r, length %r, '
                     'counter %r', track, index, path, length, counter)

        t = self.tracks[track - 1]
        i = t.indexes[index]
        start = i.absolute
        assert start is not None, "index %r is missing absolute offset" % i
        end = start + length - 1  # last sector that should come from this file

        # FIXME: check border conditions here, esp. wrt. toc's off-by-one bug
        while i.absolute <= end:
            i.path = path
            i.relative = i.absolute - start
            i.counter = counter
            logger.debug('setting path %r, relative %r on track %d, '
                         'index %d, counter %r', path, i.relative, track,
                         index, counter)
            try:
                track, index = self.getNextTrackIndex(track, index)
                t = self.tracks[track - 1]
                i = t.indexes[index]
            except IndexError:
                break

    def absolutize(self):
        """
        Calculate absolute offsets on indexes as much as possible.

        Only possible for as long as tracks draw from the same file.
        """
        t = self.tracks[0].number
        index = self.tracks[0].getFirstIndex()
        i = index.number
        # the first cut is the deepest
        counter = index.counter

        logger.debug('absolutizing')
        while True:
            track = self.tracks[t - 1]
            index = track.getIndex(i)
            assert track.number == t
            assert index.number == i
            if index.counter is None:
                logger.debug('track %d, index %d has no counter', t, i)
                break
            if index.counter != counter:
                logger.debug('track %d, index %d has a different counter',
                             t, i)
                break
            logger.debug('setting absolute offset %d on track %d, index %d',
                         index.relative, t, i)
            if index.absolute is not None:
                if index.absolute != index.relative:
                    msg = 'Track %d, index %d had absolute %d,' \
                        ' overriding with %d' % (
                            t, i, index.absolute, index.relative)
                    raise ValueError(msg)
            index.absolute = index.relative
            try:
                t, i = self.getNextTrackIndex(t, i)
            except IndexError:
                break

    def merge(self, other, session=2):
        """
        Merge the given table at the end.

        The other table is assumed to be from an additional session,

        :param other: session table
        :type other: Table
        :param session: session number
        :type session: int
        """
        gap = self._getSessionGap(session)

        trackCount = len(self.tracks)
        sourceCounter = self.tracks[-1].getLastIndex().counter

        for track in other.tracks:
            t = copy.deepcopy(track)
            t.number = track.number + trackCount
            t.session = session
            for i in list(t.indexes.values()):
                if i.absolute is not None:
                    i.absolute += self.leadout + gap
                    logger.debug('fixing track %02d, index %02d, absolute %d',
                                 t.number, i.number, i.absolute)
                if i.counter is not None:
                    i.counter += sourceCounter
                    logger.debug('fixing track %02d, index %02d, counter %d',
                                 t.number, i.number, i.counter)
            self.tracks.append(t)

        self.leadout += other.leadout + gap  # FIXME
        logger.debug('fixing leadout, now %d', self.leadout)

    @staticmethod
    def _getSessionGap(session):
        # From cdrecord multi-session info:
        # For the first additional session this is 11250 sectors
        # lead-out/lead-in overhead + 150 sectors for the pre-gap of the first
        # track after the lead-in = 11400 sectos.

        # For all further session this is 6750 sectors lead-out/lead-in
        # overhead + 150 sectors for the pre-gap of the first track after the
        # lead-in = 6900 sectors.

        gap = 11400
        if session > 2:
            gap = 6900
        return gap

    # lookups

    def getNextTrackIndex(self, track, index):
        """
        Return the next track and index.

        :param track: track number, 1-based
        :type track: int
        :raises IndexError: on last index
        :rtype: tuple(int, int)
        :param index: index of the next track
        :type index: int
        """
        t = self.tracks[track - 1]
        indexes = list(t.indexes)
        position = indexes.index(index)

        if position + 1 < len(indexes):
            return track, indexes[position + 1]

        track += 1
        if track > len(self.tracks):
            raise IndexError("No index beyond track %d, index %d" % (
                track - 1, index))

        t = self.tracks[track - 1]
        indexes = list(t.indexes)

        return track, indexes[0]

    # various tests for types of Table

    def hasTOC(self):
        """
        Check if the Table has a complete TOC.

        A TOC is a list of all tracks and their Index 01, with absolute
        offsets, as well as the leadout.
        """
        if not self.leadout:
            logger.debug('no leadout, no TOC')
            return False

        for t in self.tracks:
            if 1 not in list(t.indexes):
                logger.debug('no index 1, no TOC')
                return False
            if t.indexes[1].absolute is None:
                logger.debug('no absolute index 1, no TOC')
                return False

        return True

    def accuraterip_ids(self):
        """
        Return both AccurateRip disc ids.

        :returns: both AccurateRip disc ids as a tuple of 8-char
                  hexadecimal strings
        :rtype: tuple(str, str)
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
        offset = self.getTrackEnd(self.tracks[-1].number) + 1
        discId1 += offset
        discId2 += offset * (self.getAudioTracks() + 1)

        discId1 &= 0xffffffff
        discId2 &= 0xffffffff

        return "%08x" % discId1, "%08x" % discId2

    def accuraterip_path(self):
        discId1, discId2 = self.accuraterip_ids()
        return "%s/%s/%s/dBAR-%.3d-%s-%s-%s.bin" % (
            discId1[-1], discId1[-2], discId1[-3],
            self.getAudioTracks(), discId1, discId2, self.getCDDBDiscId()
        )

    def canCue(self):
        """Check if this table can be used to generate a .cue file."""
        if not self.hasTOC():
            logger.debug('no TOC, cannot cue')
            return False

        for t in self.tracks:
            for i in list(t.indexes.values()):
                if i.relative is None:
                    logger.debug('track %02d, Index %02d does not '
                                 'have relative', t.number, i.number)
                    return False

        return True
