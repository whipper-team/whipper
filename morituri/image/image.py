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

import gst

from morituri.common import task, crc
from morituri.image import cue

class Image:
    def __init__(self, path):
        """
        @param path: .cue path
        """
        self._path = path
        self.cue = cue.Cue(path)
        self.cue.parse()
        self._offsets = [] # 0 .. trackCount - 1
        self._lengths = [] # 0 .. trackCount - 1

    def getRealPath(self, path):
        """
        Translate the .cue's FILE to an existing path.
        """
        if os.path.exists(path):
            return path

        # .cue FILE statements have Windows-style path separators, so convert
        tpath = os.path.join(*path.split('\\'))
        # if the path is relative, make it absolute relative to the cue file
        if tpath != os.path.abspath(tpath):
            tpath = os.path.join(os.path.dirname(self._path), tpath)

        noext, _ = os.path.splitext(tpath)
        for ext in ['wav', 'flac']:
            cpath = '%s.%s' % (noext, ext)
            if os.path.exists(cpath):
                return cpath

        raise KeyError, "Cannot find file for %s" % path

    def setup(self, runner):
        """
        Do initial setup, like figuring out track lengths.
        """
        verify = ImageVerifyTask(self)
        runner.run(verify)

        # calculate offset and length for each track

        # CD's have a standard lead-in time of 2 seconds
        offset = 2 * crc.DISC_FRAMES_PER_SECOND \
            + self.cue.tracks[0].getIndex(1)[0]

        for i in range(len(self.cue.tracks)):
            self._offsets.append(offset)
            length = self.cue.getTrackLength(self.cue.tracks[i])
            if length == -1:
                length = verify.lengths[i + 1]
            self._lengths.append(length)

            offset += length

    def getTrackOffset(self, track):
        return self._offsets[self.cue.tracks.index(track)]

    def getTrackLength(self, track):
        return self._lengths[self.cue.tracks.index(track)]

    def _cddbSum(self, i):
        ret = 0
        while i > 0:
            ret += (i % 10)
            i /= 10

        return ret

    def cddbDiscId(self):
        n = 0

        for track in self.cue.tracks:
            offset = self.getTrackOffset(track)
            seconds = offset / crc.DISC_FRAMES_PER_SECOND
            n += self._cddbSum(seconds)

        last = self.cue.tracks[-1]
        leadout = self.getTrackOffset(last) + self.getTrackLength(last)
        frameLength = leadout - self.getTrackOffset(self.cue.tracks[0])
        t = frameLength / crc.DISC_FRAMES_PER_SECOND

        value = (n % 0xff) << 24 | t << 8 | len(self.cue.tracks)
        
        return "%08x" % value

class MultiTask(task.Task):
    """
    I perform multiple tasks.
    I track progress of each individual task, going back to 0 for each task.
    """

    description = 'Doing various tasks'
    tasks = None

    def addTask(self, task):
        if self.tasks is None:
            self.tasks = []
        self.tasks.append(task)

    def start(self, runner):
        task.Task.start(self, runner)

        # initialize task tracking
        self._task = 0
        self.__tasks = self.tasks[:]
        self._generic = self.description

        self._next()

    def _next(self):
        # start next task
        self.progress = 0.0 # reset progress for each task
        task = self.__tasks[0]
        del self.__tasks[0]
        self._task += 1
        self.description = "%s (%d of %d) ..." % (
            self._generic, self._task, len(self.tasks))
        task.addListener(self)
        task.start(self.runner)
        
    ### listener methods
    def started(self, task):
        pass

    def progressed(self, task, value):
        self.setProgress(value)

    def stopped(self, task):
        if not self.__tasks:
            self.stop()
            return

        # pick another
        self._next()


class AudioRipCRCTask(MultiTask):
    """
    I calculate the AudioRip CRC's of all tracks.
    """
    
    description = "CRC'ing tracks"

    def __init__(self, image):
        self._image = image
        cue = image.cue
        self.crcs = []

        for trackIndex, track in enumerate(cue.tracks):
            index = track._indexes[1]
            length = cue.getTrackLength(track)
            file = index[1]
            offset = index[0]

            path = image.getRealPath(file.path)
            crctask = crc.CRCAudioRipTask(path,
                trackNumber=trackIndex + 1, trackCount=len(cue.tracks),
                frameStart=offset * crc.FRAMES_PER_DISC_FRAME,
                frameLength=length * crc.FRAMES_PER_DISC_FRAME)
            self.addTask(crctask)

    def stop(self):
        self.crcs = [t.crc for t in self.tasks]
        MultiTask.stop(self)

class AudioLengthTask(task.Task):
    """
    I calculate the length of a track in audio frames.

    @ivar  length: length of the decoded audio file, in audio frames.
    """

    length = None

    def __init__(self, path):
        self._path = path

    def debug(self, *args, **kwargs):
        return
        print args, kwargs

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
        self.debug('total length', length)
        self.length = length
        self._pipeline.set_state(gst.STATE_NULL)
        
        self.stop()

class ImageVerifyTask(MultiTask):
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
            index = track._indexes[1]
            offset = index[0]
            length = cue.getTrackLength(track)
            file = index[1]

            if length == -1:
                path = image.getRealPath(file.path)
                taskk = AudioLengthTask(path)
                self.addTask(taskk)
                self._tasks.append((trackIndex + 1, track, taskk))

    def stop(self):
        for trackIndex, track, taskk in self._tasks:
            # print '%d has length %d' % (trackIndex, taskk.length)
            index = track._indexes[1]
            offset = index[0]
            assert taskk.length % crc.FRAMES_PER_DISC_FRAME == 0
            end = taskk.length / crc.FRAMES_PER_DISC_FRAME
            self.lengths[trackIndex] = end - offset

        MultiTask.stop(self)
