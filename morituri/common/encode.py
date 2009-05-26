# -*- Mode: Python; test-case-name: morituri.test.test_common_encode -*-
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

import os
import struct
import zlib

import gst

from morituri.common import common, task

from morituri.common import log
log.init()

class EncodeTask(task.Task):
    """
    I am a task that encodes a .wav file.
    I set tags too.
    """

    description = 'Encoding'

    def __init__(self, inpath, outpath, taglist=None):
        """
        """
        self._inpath = inpath
        self._outpath = outpath
        self._taglist = taglist

    def start(self, runner):
        task.Task.start(self, runner)
        self._pipeline = gst.parse_launch('''
            filesrc location="%s" !
            decodebin name=decoder ! audio/x-raw-int !
            flacenc name=muxer !
            filesink location="%s" name=sink''' % (self._inpath, self._outpath))


        # set tags
        if self._taglist:
            muxer = self._pipeline.get_by_name('muxer')
            muxer.merge_tags(self._taglist, gst.TAG_MERGE_APPEND)

        self.debug('pausing pipeline')
        self._pipeline.set_state(gst.STATE_PAUSED)
        self._pipeline.get_state()
        self.debug('paused pipeline')

        # get length
        decoder = self._pipeline.get_by_name('decoder')
        self.debug('query duration')
        length, format = muxer.query_duration(gst.FORMAT_DEFAULT)
        # wavparse 0.10.14 returns in bytes
        if format == gst.FORMAT_BYTES:
            self.debug('query returned in BYTES format')
            length /= 4
        self.debug('total length: %r', length)
        self._length = length

        # add a probe so we can track progress
        sinkpad = muxer.get_pad('sink')
        srcpad = sinkpad.get_peer()
        srcpad.add_buffer_probe(self._probe_handler, False)

        # add eos handling
        bus = self._pipeline.get_bus()
        bus.add_signal_watch()
        bus.connect('message::eos', self._eos_cb)

        self.debug('scheduling setting to play')
        # since set_state returns non-False, adding it as timeout_add
        # will repeatedly call it, and block the main loop; so
        #   gobject.timeout_add(0L, self._pipeline.set_state, gst.STATE_PLAYING)
        # would not work.

        def play():
            self._pipeline.set_state(gst.STATE_PLAYING)
            return False
        self.runner.schedule(0, play)

        #self._pipeline.set_state(gst.STATE_PLAYING)
        self.debug('scheduled setting to play')

    def _probe_handler(self, pad, buffer, ret):
        # marshal to main thread
        self.runner.schedule(0, self.setProgress,
            float(buffer.offset) / self._length)
        return True

    def _eos_cb(self, bus, message):
        self.debug('eos, scheduling stop')
        self.runner.schedule(0, self.stop)

    def stop(self):
        self.debug('stopping')
        self.debug('setting state to NULL')
        self._pipeline.set_state(gst.STATE_NULL)
        self.debug('set state to NULL')
        task.Task.stop(self)
