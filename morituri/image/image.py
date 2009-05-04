# -*- Mode: Python; test-case-name: morituri.test.test_image_image -*-
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
Wrap on-disk CD images based on the .cue file.
"""

import os
import struct

import gst

from morituri.common import task, checksum, log
from morituri.image import cue, table

from morituri.test import common

class Image(object, log.Loggable):
    """
    @ivar table: The Table of Contents for this image.
    @type table: L{table.Table}
    """

    def __init__(self, path):
        """
        @param path: .cue path
        """
        self._path = path
        self.cue = cue.Cue(path)
        self.cue.parse()
        self._offsets = [] # 0 .. trackCount - 1
        self._lengths = [] # 0 .. trackCount - 1

        self.table = None

    def getRealPath(self, path):
        """
        Translate the .cue's FILE to an existing path.
        """
        return self.cue.getRealPath(path)

    def setup(self, runner):
        """
        Do initial setup, like figuring out track lengths, and
        constructing the Table of Contents.
        """
        self.debug('setup image start')
        verify = ImageVerifyTask(self)
        self.debug('verifying image')
        runner.run(verify)
        self.debug('verified image')

        # calculate offset and length for each track

        # CD's have a standard lead-in time of 2 seconds;
        # checksums that use it should add it there
        offset = self.cue.tracks[0].getIndex(1).relative

        tracks = []

        for i in range(len(self.cue.tracks)):
            length = self.cue.getTrackLength(self.cue.tracks[i])
            if length == -1:
                length = verify.lengths[i + 1]
            t = table.ITTrack(i + 1, audio=True)
            tracks.append(t)
            # FIXME: this probably only works for non-compliant .CUE files
            # where pregap is put at end of previous file
            t.index(1, absolute=offset, path=self.cue.tracks[i].getIndex(1).path,
                relative=0)

            offset += length

        self.table = table.IndexTable(tracks)
        self.table.leadout = offset
        self.debug('setup image done')


class AccurateRipChecksumTask(task.MultiSeparateTask):
    """
    I calculate the AccurateRip checksums of all tracks.
    """
    
    description = "Checksumming tracks"

    def __init__(self, image):
        self._image = image
        cue = image.cue
        self.checksums = []

        self.debug('Checksumming %d tracks' % len(cue.tracks))
        for trackIndex, track in enumerate(cue.tracks):
            index = track.indexes[1]
            length = cue.getTrackLength(track)
            self.debug('track %d has length %d' % (trackIndex + 1, length))

            path = image.getRealPath(index.path)
            checksumTask = checksum.AccurateRipChecksumTask(path,
                trackNumber=trackIndex + 1, trackCount=len(cue.tracks),
                frameStart=index.relative * checksum.SAMPLES_PER_FRAME,
                frameLength=length * checksum.SAMPLES_PER_FRAME)
            self.addTask(checksumTask)

    def stop(self):
        self.checksums = [t.checksum for t in self.tasks]
        task.MultiSeparateTask.stop(self)

class AudioLengthTask(task.Task):
    """
    I calculate the length of a track in audio frames.

    @ivar  length: length of the decoded audio file, in audio frames.
    """

    length = None

    def __init__(self, path):
        self._path = path

    def start(self, runner):
        task.Task.start(self, runner)
        self._pipeline = gst.parse_launch('''
            filesrc location="%s" !
            decodebin ! audio/x-raw-int !
            fakesink name=sink''' % self._path)
        self.debug('pausing')
        self._pipeline.set_state(gst.STATE_PAUSED)
        self._pipeline.get_state()
        self.debug('paused')

        self.debug('query duration')
        sink = self._pipeline.get_by_name('sink')
        assert sink, 'Error constructing pipeline'

        length, format = sink.query_duration(gst.FORMAT_DEFAULT)
        # wavparse 0.10.14 returns in bytes
        if format == gst.FORMAT_BYTES:
            self.debug('query returned in BYTES format')
            length /= 4
        self.debug('total length of %s in samples: %d', self._path, length)
        self.length = length
        self._pipeline.set_state(gst.STATE_NULL)
        
        self.stop()

class ImageVerifyTask(task.MultiSeparateTask):
    """
    I verify a disk image and get the necessary track lengths.
    """
    
    description = "Checking tracks"
    lengths = None

    def __init__(self, image):
        self._image = image
        cue = image.cue
        self._tasks = []
        self.lengths = {}

        for trackIndex, track in enumerate(cue.tracks):
            self.debug('verifying track %d', trackIndex + 1)
            index = track.indexes[1]
            length = cue.getTrackLength(track)

            if length == -1:
                path = image.getRealPath(index.path)
                self.debug('schedule scan of audio length of %s', path)
                taskk = AudioLengthTask(path)
                self.addTask(taskk)
                self._tasks.append((trackIndex + 1, track, taskk))
            else:
                self.debug('track %d has length %d', trackIndex + 1, length)

    def stop(self):
        for trackIndex, track, taskk in self._tasks:
            # print '%d has length %d' % (trackIndex, taskk.length)
            index = track.indexes[1]
            assert taskk.length % checksum.SAMPLES_PER_FRAME == 0
            end = taskk.length / checksum.SAMPLES_PER_FRAME
            self.lengths[trackIndex] = end - index.relative

        task.MultiSeparateTask.stop(self)

# FIXME: move this method to a different module ?
def getAccurateRipResponses(data):
    ret = []

    while data:
        trackCount = struct.unpack("B", data[0])[0]
        bytes = 1 + 12 + trackCount * (1 + 8)

        ret.append(AccurateRipResponse(data[:bytes]))
        data = data[bytes:]

    return ret

class AccurateRipResponse(object):
    """
    I represent the response of the AccurateRip online database.
    """

    trackCount = None
    discId1 = ""
    discId2 = ""
    cddbDiscId = ""
    confidences = None
    checksums = None

    def __init__(self, data):
        self.trackCount = struct.unpack("B", data[0])[0]
        self.discId1 = "%08x" % struct.unpack("<L", data[1:5])[0]
        self.discId2 = "%08x" % struct.unpack("<L", data[5:9])[0]
        self.cddbDiscId = "%08x" % struct.unpack("<L", data[9:13])[0]

        self.confidences = []
        self.checksums = []

        pos = 13
        for i in range(self.trackCount):
            confidence = struct.unpack("B", data[pos])[0]
            checksum = "%08x" % struct.unpack("<L", data[pos + 1:pos + 5])[0]
            pos += 9
            self.confidences.append(confidence)
            self.checksums.append(checksum)
