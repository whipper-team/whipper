# -*- Mode: Python; test-case-name: whipper.test.test_image_image -*-
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

"""
Wrap on-disk CD images based on the .cue file.
"""

import os

from whipper.common import encode
from whipper.common import common
from whipper.image import cue, table
from whipper.extern.task import task
from whipper.program.soxi import AudioLengthTask

import logging
logger = logging.getLogger(__name__)


class Image:
    """
    :ivar table:    The Table of Contents for this image.
    :vartype table: table.Table
    """
    logCategory = 'Image'

    def __init__(self, path):
        """
        :type  path: str
        :param path: .cue path
        """
        assert isinstance(path, str), "%r is not str" % path

        self._path = path
        self.cue = cue.CueFile(path)
        self.cue.parse()
        self._offsets = []  # 0 .. trackCount - 1
        self._lengths = []  # 0 .. trackCount - 1

        self.table = None

    def getRealPath(self, path):
        """
        Translate the .cue's FILE to an existing path.

        :param path: .cue path
        """
        assert isinstance(path, str), "%r is not str" % path

        return self.cue.getRealPath(path)

    def setup(self, runner):
        """
        Do initial setup, like figuring out track lengths, and
        constructing the Table of Contents.
        """
        logger.debug('setup image start')
        verify = ImageVerifyTask(self)
        logger.debug('verifying image')
        runner.run(verify)
        logger.debug('verified image')

        # calculate offset and length for each track

        # CD's have a standard lead-in time of 2 seconds;
        # checksums that use it should add it there
        if 0 in verify.lengths:
            offset = verify.lengths[0]
        else:
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
        logger.debug('setup image done')


class ImageVerifyTask(task.MultiSeparateTask):
    """
    I verify a disk image and get the necessary track lengths.
    """

    logCategory = 'ImageVerifyTask'

    description = "Checking tracks"
    lengths = None

    def __init__(self, image):
        task.MultiSeparateTask.__init__(self)

        self._image = image
        # XXX: Pylint, redefining name 'cue' from outer scope (import)
        cue = image.cue
        self._tasks = []
        self.lengths = {}

        try:
            htoa = cue.table.tracks[0].indexes[0]
            track = cue.table.tracks[0]
            path = image.getRealPath(htoa.path)
            assert isinstance(path, str), "%r is not str" % path
            logger.debug('schedule scan of audio length of %r', path)
            taskk = AudioLengthTask(path)
            self.addTask(taskk)
            self._tasks.append((0, track, taskk))
        except (KeyError, IndexError):
            logger.debug('no HTOA track')

        for trackIndex, track in enumerate(cue.table.tracks):
            logger.debug('verifying track %d', trackIndex + 1)
            index = track.indexes[1]
            length = cue.getTrackLength(track)

            if length == -1:
                path = image.getRealPath(index.path)
                assert isinstance(path, str), "%r is not str" % path
                logger.debug('schedule scan of audio length of %r', path)
                taskk = AudioLengthTask(path)
                self.addTask(taskk)
                self._tasks.append((trackIndex + 1, track, taskk))
            else:
                logger.debug('track %d has length %d', trackIndex + 1, length)

    def stop(self):
        for trackIndex, track, taskk in self._tasks:
            if taskk.exception:
                logger.debug('subtask %r had exception %r, shutting down',
                             taskk, taskk.exception)
                self.setException(taskk.exception)
                break

            if taskk.length is None:
                raise ValueError("Track length was not found; "
                                 "look for earlier errors "
                                 "in debug log (set RIP_DEBUG=4)")
            index = track.indexes[1]
            assert taskk.length % common.SAMPLES_PER_FRAME == 0
            end = taskk.length // common.SAMPLES_PER_FRAME
            self.lengths[trackIndex] = end - index.relative

        task.MultiSeparateTask.stop(self)


class ImageEncodeTask(task.MultiSeparateTask):
    """
    I encode a disk image to a different format.
    """

    description = "Encoding tracks"

    def __init__(self, image, outdir):
        task.MultiSeparateTask.__init__(self)

        self._image = image
        # XXX: Pylint, redefining name 'cue' from outer scope (import)
        cue = image.cue
        self._tasks = []
        self.lengths = {}

        def add(index):

            path = image.getRealPath(index.path)
            assert isinstance(path, str), "%r is not str" % path
            logger.debug('schedule encode of %r', path)
            root, _ = os.path.splitext(os.path.basename(path))
            outpath = os.path.join(outdir, root + '.' + 'flac')
            logger.debug('schedule encode to %r', outpath)
            taskk = encode.FlacEncodeTask(
                path, os.path.join(outdir, root + '.' + 'flac'))
            self.addTask(taskk)

        try:
            htoa = cue.table.tracks[0].indexes[0]
            logger.debug('encoding HTOA track')
            add(htoa)
        except (KeyError, IndexError):
            logger.debug('no HTOA track')

        for trackIndex, track in enumerate(cue.table.tracks):
            logger.debug('encoding track %d', trackIndex + 1)
            index = track.indexes[1]
            add(index)
