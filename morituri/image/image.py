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

from morituri.common import log, common
from morituri.image import cue, table

from morituri.extern.task import task, gstreamer


class Image(object, log.Loggable):
    """
    @ivar table: The Table of Contents for this image.
    @type table: L{table.Table}
    """
    logCategory = 'Image'

    def __init__(self, path):
        """
        @type  path: unicode
        @param path: .cue path
        """
        assert type(path) is unicode, "%r is not unicode" % path

        self._path = path
        self.cue = cue.CueFile(path)
        self.cue.parse()
        self._offsets = [] # 0 .. trackCount - 1
        self._lengths = [] # 0 .. trackCount - 1

        self.table = None

    def getRealPath(self, path):
        """
        Translate the .cue's FILE to an existing path.

        @param path: .cue path
        """
        assert type(path) is unicode, "%r is not unicode" % path

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
        offset = self.cue.table.tracks[0].getIndex(1).relative

        tracks = []

        for i in range(len(self.cue.table.tracks)):
            length = self.cue.getTrackLength(self.cue.table.tracks[i])
            if length == -1:
                length = verify.lengths[i + 1]
            t = table.Track(i + 1, audio=True)
            tracks.append(t)
            # FIXME: this probably only works for non-compliant .CUE files
            # where pregap is put at end of previous file
            t.index(1, absolute=offset,
                path=self.cue.table.tracks[i].getIndex(1).path,
                relative=0)

            offset += length

        self.table = table.Table(tracks)
        self.table.leadout = offset
        self.debug('setup image done')


class AccurateRipChecksumTask(log.Loggable, task.MultiSeparateTask):
    """
    I calculate the AccurateRip checksums of all tracks.
    """

    description = "Checksumming tracks"

    def __init__(self, image):
        task.MultiSeparateTask.__init__(self)

        self._image = image
        cue = image.cue
        self.checksums = []

        self.debug('Checksumming %d tracks' % len(cue.table.tracks))
        for trackIndex, track in enumerate(cue.table.tracks):
            index = track.indexes[1]
            length = cue.getTrackLength(track)
            self.debug('track %d has length %d' % (trackIndex + 1, length))

            path = image.getRealPath(index.path)

            # here to avoid import gst eating our options
            from morituri.common import checksum

            checksumTask = checksum.AccurateRipChecksumTask(path,
                trackNumber=trackIndex + 1, trackCount=len(cue.table.tracks),
                frameStart=index.relative * common.SAMPLES_PER_FRAME,
                frameLength=length * common.SAMPLES_PER_FRAME)
            self.addTask(checksumTask)

    def stop(self):
        self.checksums = [t.checksum for t in self.tasks]
        task.MultiSeparateTask.stop(self)


class AudioLengthTask(log.Loggable, gstreamer.GstPipelineTask):
    """
    I calculate the length of a track in audio frames.

    @ivar  length: length of the decoded audio file, in audio frames.
    """
    logCategory = 'AudioLengthTask'
    description = 'Getting length of audio track'
    length = None

    playing = False

    def __init__(self, path):
        """
        @type  path: unicode
        """
        assert type(path) is unicode, "%r is not unicode" % path

        self._path = path
        self.logName = os.path.basename(path).encode('utf-8')

    def getPipelineDesc(self):
        return '''
            filesrc location="%s" !
            decodebin ! audio/x-raw-int !
            fakesink name=sink''' % \
                gstreamer.quoteParse(self._path).encode('utf-8')

    def paused(self):
        self.debug('query duration')
        sink = self.pipeline.get_by_name('sink')
        assert sink, 'Error constructing pipeline'

        try:
            length, qformat = sink.query_duration(self.gst.FORMAT_DEFAULT)
        except self.gst.QueryError, e:
            self.info('failed to query duration of %r' % self._path)
            self.setException(e)
            raise

        # wavparse 0.10.14 returns in bytes
        if qformat == self.gst.FORMAT_BYTES:
            self.debug('query returned in BYTES format')
            length /= 4
        self.debug('total length of %r in samples: %d', self._path, length)
        self.length = length

        self.pipeline.set_state(self.gst.STATE_NULL)
        self.stop()


class ImageVerifyTask(log.Loggable, task.MultiSeparateTask):
    """
    I verify a disk image and get the necessary track lengths.
    """

    logCategory = 'ImageVerifyTask'

    description = "Checking tracks"
    lengths = None

    def __init__(self, image):
        task.MultiSeparateTask.__init__(self)

        self._image = image
        cue = image.cue
        self._tasks = []
        self.lengths = {}

        for trackIndex, track in enumerate(cue.table.tracks):
            self.debug('verifying track %d', trackIndex + 1)
            index = track.indexes[1]
            length = cue.getTrackLength(track)

            if length == -1:
                path = image.getRealPath(index.path)
                assert type(path) is unicode, "%r is not unicode" % path
                self.debug('schedule scan of audio length of %r', path)
                taskk = AudioLengthTask(path)
                self.addTask(taskk)
                self._tasks.append((trackIndex + 1, track, taskk))
            else:
                self.debug('track %d has length %d', trackIndex + 1, length)

    def stop(self):
        for trackIndex, track, taskk in self._tasks:
            if taskk.exception:
                self.debug('subtask %r had exception %r, shutting down' % (
                    taskk, taskk.exception))
                self.setException(taskk.exception)
                break

            # print '%d has length %d' % (trackIndex, taskk.length)
            index = track.indexes[1]
            assert taskk.length % common.SAMPLES_PER_FRAME == 0
            end = taskk.length / common.SAMPLES_PER_FRAME
            self.lengths[trackIndex] = end - index.relative

        task.MultiSeparateTask.stop(self)


class ImageEncodeTask(log.Loggable, task.MultiSeparateTask):
    """
    I encode a disk image to a different format.
    """

    description = "Encoding tracks"

    def __init__(self, image, profile, outdir):
        task.MultiSeparateTask.__init__(self)

        self._image = image
        self._profile = profile
        cue = image.cue
        self._tasks = []
        self.lengths = {}

        def add(index):
            # here to avoid import gst eating our options
            from morituri.common import encode

            path = image.getRealPath(index.path)
            assert type(path) is unicode, "%r is not unicode" % path
            self.debug('schedule encode of %r', path)
            root, ext = os.path.splitext(os.path.basename(path))
            outpath = os.path.join(outdir, root + '.' + profile.extension)
            self.debug('schedule encode to %r', outpath)
            taskk = encode.EncodeTask(path, os.path.join(outdir,
                root + '.' + profile.extension), profile)
            self.addTask(taskk)

        try:
            htoa = cue.table.tracks[0].indexes[0]
            self.debug('encoding htoa track')
            add(htoa)
        except (KeyError, IndexError):
            self.debug('no htoa track')
            pass

        for trackIndex, track in enumerate(cue.table.tracks):
            self.debug('encoding track %d', trackIndex + 1)
            index = track.indexes[1]
            add(index)
