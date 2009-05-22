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

from morituri.common import task, common, log

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
    I represent a track entry in an Table.

    @ivar number:  track number (1-based)
    @type number:  int
    @ivar audio:   whether the track is audio
    @type audio:   bool
    @type indexes: dict of number -> L{Index}
    @ivar isrc:    ISRC code (12 alphanumeric characters)
    @type isrc:    str
    """

    number = None
    audio = None
    indexes = None
    isrc = None
    cdtext = None

    def __repr__(self):
        return '<Track %02d>' % self.number

    def __init__(self, number, audio=True):
        self.number = number
        self.audio = audio
        self.indexes = {}
        self.cdtext = {}

    def index(self, number, absolute=None, path=None, relative=None, counter=None):
        i = Index(number, absolute, path, relative, counter)
        self.indexes[number] = i

    def getIndex(self, number):
        return self.indexes[number]

    def getFirstIndex(self):
        indexes = self.indexes.keys()
        indexes.sort()
        return self.indexes[indexes[0]]

class Index:
    """
    @ivar counter: counter for the index source; distinguishes between
                   the matching FILE lines in .cue files for example
    """
    number = None
    absolute = None
    path = None
    relative = None
    counter = None

    def __init__(self, number, absolute=None, path=None, relative=None, counter=None):
        self.number = number
        self.absolute = absolute
        self.path = path
        self.relative = relative
        self.counter = counter

    def __repr__(self):
        return '<Index %02d, absolute %r, path %r, relative %r, counter %r>' % (
            self.number, self.absolute, self.path, self.relative, self.counter)

class Table(object, log.Loggable):
    """
    I represent a table of indexes on a CD.

    @ivar tracks: tracks on this CD
    @type tracks: list of L{Track}
    @ivar catalog: catalog number
    @type catalog: str
    """

    tracks = None # list of Track
    leadout = None # offset where the leadout starts
    catalog = None # catalog number; FIXME: is this UPC ?
    cdtext = None

    def __init__(self, tracks=None):
        if not tracks:
            tracks = []

        self.tracks = tracks
        self.cdtext = {}

    def getTrackStart(self, number):
        """
        @param number: the track number, 1-based
        @type  number: int

        @returns: the start of the given track number's index 1, in CD frames
        @rtype:   int
        """
        track = self.tracks[number - 1]
        return track.getIndex(1).absolute

    def getTrackEnd(self, number):
        """
        @param number: the track number, 1-based
        @type  number: int

        @returns: the end of the given track number (ie index 1 of next track)
        @rtype:   int
        """
        end = self.leadout - 1
        if number < len(self.tracks):
            end = self.tracks[number].getIndex(1).absolute - 1
        return end

    def getTrackLength(self, number):
        """
        @param number: the track number, 1-based
        @type  number: int

        @returns: the length of the given track number, in CD frames
        @rtype:   int
        """
        return self.getTrackEnd(number) - self.getTrackStart(number) + 1

    def getAudioTracks(self):
        """
        @returns: the number of audio tracks on the CD
        @rtype:   int
        """
        return len([t for t in self.tracks if t.audio])

    def hasDataTracks(self):
        """
        @returns: whether this disc contains data tracks
        """
        return len([t for t in self.tracks if not t.audio]) > 0


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

        # CD's have a standard lead-in time of 2 seconds
        # which gets added for CDDB disc id's
        delta = 2 * common.FRAMES_PER_SECOND
        #if self.getTrackStart(1) > 0:
        #    delta = 0

        debug = [str(len(self.tracks))]
        for track in self.tracks:
            offset = self.getTrackStart(track.number) + delta
            debug.append(str(offset))
            seconds = offset / common.FRAMES_PER_SECOND
            n += self._cddbSum(seconds)

        last = self.tracks[-1]
        # the 'real' leadout, not offset by 150 frames
        # print 'THOMAS: disc leadout', self.leadout
        leadout = self.getTrackEnd(last.number) + 1
        self.debug('leadout LBA: %d', leadout)
        startSeconds = self.getTrackStart(1) / common.FRAMES_PER_SECOND
        leadoutSeconds = leadout / common.FRAMES_PER_SECOND
        t = leadoutSeconds - startSeconds
        debug.append(str(leadoutSeconds + 2)) # 2 is the 150 frame cddb offset

        value = (n % 0xff) << 24 | t << 8 | len(self.tracks)

        # compare this debug line to cd-discid output
        self.debug('cddb disc id debug: %s',
            " ".join(["%08x" % value, ] + debug))
        
        return "%08x" % value

    def getMusicBrainzDiscId(self):
        """
        Calculate the MusicBrainz disc ID.

        @rtype:   str
        @returns: the 28-character base64-encoded disc ID
        """
        # MusicBrainz disc id does not take into account data tracks
        import sha
        import base64

        sha1 = sha.new()

        # number of first track
        sha1.update("%02X" % 1)

        # number of last track
        sha1.update("%02X" % self.getAudioTracks())

        leadout = self.leadout
        # if the disc is multi-session, last track is the data track,
        # and we should subtract 11250 + 150 from the last track's offset
        # for the leadout
        if self.hasDataTracks():
            assert not self.tracks[-1].audio
            leadout = self.tracks[-1].getIndex(1).absolute - 11250 - 150

        # treat leadout offset as track 0 offset
        sha1.update("%08X" % (150 + leadout))

        # offsets of tracks
        for i in range(1, 100):
            try:
                offset = self.tracks[i - 1].getIndex(1).absolute + 150
            except IndexError:
                #print 'track', i - 1, '0 offset'
                offset = 0
            sha1.update("%08X" % offset)

        digest = sha1.digest()
        assert len(digest) == 20, \
            "digest should be 20 chars, not %d" % len(digest)

        # The RFC822 spec uses +, /, and = characters, all of which are special
        # HTTP/URL characters. To avoid the problems with dealing with that, I
        # (Rob) used ., _, and -

        # base64 altchars specify replacements for + and /
        result = base64.b64encode(digest, '._')

        # now replace =
        result = "-".join(result.split("="))
        assert len(result) == 28, \
            "Result should be 28 characters, not %d" % len(result)

        return result

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

    def cue(self, program='Morituri'):
        """
        Dump our internal representation to a .cue file content.
        """
        lines = []

        # header
        main = ['PERFORMER', 'TITLE']

        for key in CDTEXT_FIELDS:
                if key not in main and self.cdtext.has_key(key):
                    lines.append("    %s %s" % (key, self.cdtext[key]))

        assert self.hasTOC(), "Table does not represent a full CD TOC"
        lines.append('REM DISCID %s' % self.getCDDBDiscId().upper())
        lines.append('REM COMMENT "%s"' % program)

        if self.catalog:
            lines.append("CATALOG %s" % self.catalog)

        for key in main:
            if self.cdtext.has_key(key):
                lines.append('%s "%s"' % (key, self.cdtext[key]))

        # add the first FILE line
        path = self.tracks[0].getFirstIndex().path
        counter = self.tracks[0].getFirstIndex().counter
        lines.append('FILE "%s" WAVE' % path)

        for i, track in enumerate(self.tracks):
            # if there is no index 0, but there is a new file, advance
            # FILE line here
            if not track.indexes.has_key(0):
                index = track.indexes[1]
                if index.counter != counter:
                    lines.append('FILE "%s" WAVE' % index.path)
                    counter = index.counter
            lines.append("  TRACK %02d %s" % (i + 1, 'AUDIO'))
            for key in CDTEXT_FIELDS:
                if track.cdtext.has_key(key):
                    lines.append('    %s "%s"' % (key, track.cdtext[key]))

            if track.isrc is not None:
                lines.append("    ISRC %s" % track.isrc)

            indexes = track.indexes.keys()
            indexes.sort()

            for number in indexes:
                index = track.indexes[number]
                if index.counter != counter:
                    lines.append('FILE "%s" WAVE' % index.path)
                    counter = index.counter
                lines.append("    INDEX %02d %s" % (number,
                    common.framesToMSF(index.relative)))

        lines.append("")

        return "\n".join(lines) 

    ### methods that modify the table
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

        self.debug('clearing path')
        while True:
            track = self.tracks[t - 1]
            index = track.getIndex(i)
            self.debug('Clearing path on track %d, index %d', t, i)
            index.path = None
            index.relative = None
            try:
                t, i = self.getNextTrackIndex(t, i)
            except IndexError:
                break


    def setFile(self, track, index, path, length, counter=None):
        """
        Sets the given file as the source from the given index on.
        Will loop over all indexes that fall within the given length,
        to adjust the path.

        Assumes all indexes have an absolute offset and will raise if not.
        """
        self.debug('setFile: track %d, index %d, path %s, '
            'length %r, counter %r', track, index, path, length, counter)

        t = self.tracks[track - 1]
        i = t.indexes[index]
        start = i.absolute
        assert start is not None, "index %r is missing absolute offset" % i
        end = start + length - 1 # last sector that should come from this file

        # FIXME: check border conditions here, esp. wrt. toc's off-by-one bug
        while i.absolute <= end:
            i.path = path
            i.relative = i.absolute - start
            i.counter = counter
            self.debug('Setting path %s, relative %r on '
                'track %d, index %d, counter %r',
                path, i.relative, track, index, counter)
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

        #for t in self.tracks: print t, t.indexes
        self.debug('absolutizing')
        while True:
            track = self.tracks[t - 1]
            index = track.getIndex(i)
            assert track.number == t
            assert index.number == i
            if index.counter is None:
                self.debug('Track %d, index %d has no counter', t, i)
                break
            if  index.counter != counter:
                self.debug('Track %d, index %d has a different counter', t, i)
                break
            self.debug('Setting absolute offset %d on track %d, index %d',
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

    ### lookups
    def getNextTrackIndex(self, track, index):
        """
        Return the next track and index.

        @param track: track number, 1-based

        @raises IndexError: on last index

        @rtype: tuple of (int, int)
        """
        t = self.tracks[track - 1]
        indexes = t.indexes.keys()
        position = indexes.index(index)

        if position + 1 < len(indexes):
            return track, indexes[position + 1]

        track += 1
        if track > len(self.tracks):
            raise IndexError, "No index beyond track %d, index %d" % (
                track - 1, index)

        t = self.tracks[track - 1]
        indexes = t.indexes.keys()

        return track, indexes[0]


    # various tests for types of Table
    def hasTOC(self):
        """
        Check if the Table has a complete TOC.
        a TOC is a list of all tracks and their Index 01, with absolute
        offsets, as well as the leadout.
        """
        if not self.leadout:
            self.debug('no leadout, no TOC')
            return False

        for t in self.tracks:
            if 1 not in t.indexes.keys():
                self.debug('no index 1, no TOC')
                return False
            if t.indexes[1].absolute is None:
                self.debug('no absolute index 1, no TOC')
                return False

        return True
