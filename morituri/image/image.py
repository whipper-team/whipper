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

class AudioRipCRCTask(task.Task):
    """
    I calculate the AudioRip CRC's of all tracks.
    """
    def __init__(self, image):
        self._image = image
        cue = image.cue
        self._tasks = []
        self._track = 0
        self._tracks = len(cue.tracks)
        self.description = "CRC'ing %d tracks..." % len(cue.tracks)
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

            self._tasks.append(crctask)

    def start(self):
        task.Task.start(self)
        self._next()

    def _next(self):
        # start next task
        task = self._tasks[0]
        del self._tasks[0]
        self._track += 1
        self.description = "CRC'ing track %2d of %d..." % (
            self._track, self._tracks)
        task.addListener(self)
        task.start()
        
    ### listener methods
    def started(self, task):
        pass

    def progressed(self, task, value):
        self.setProgress(value)

    def stopped(self, task):
        self.crcs.append(task.crc)
        if not self._tasks:
            self.stop()
            return

        # pick another
        self.start()
