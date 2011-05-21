# -*- Mode: Python; test-case-name: morituri.test.test_common_gstreamer -*-
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

class GstException(Exception):
    def __init__(self, gerror, debug):
        self.args = (gerror, debug, )
        self.gerror = gerror
        self.debug = debug

class GstPipelineTask(task.Task):
    """
    I am a base class for tasks that use a GStreamer pipeline.

    I handle errors and raise them appropriately.
    """
    def start(self, runner):
        task.Task.start(self, runner)
        desc = self.getPipelineDesc()

        self.debug('creating pipeline %r', desc)
        self.pipeline = gst.parse_launch(desc)

        self._bus = self.pipeline.get_bus()
        gst.debug('got bus %r' % self._bus)

        # a signal watch calls callbacks from an idle loop
        # self._bus.add_signal_watch()

        # sync emission triggers sync-message signals which calls callbacks
        # from the thread that signals, but happens immediately
        self._bus.enable_sync_message_emission()
        self._bus.connect('sync-message::eos', self.bus_eos_cb)
        self._bus.connect('sync-message::tag', self.bus_tag_cb)
        self._bus.connect('sync-message::error', self.bus_error_cb)

        self.parsed()

        self.debug('pausing pipeline')
        self.pipeline.set_state(gst.STATE_PAUSED)
        self.pipeline.get_state()
        self.debug('paused pipeline')

        if not self.exception:
            self.paused()
        else:
            raise self.exception

    def getPipelineDesc(self):
        raise NotImplementedError

    def parsed(self):
        """
        Called after parsing the pipeline but before setting it to paused.
        """
        pass

    def paused(self):
        """
        Called after pipeline is paused
        """
        pass

    def bus_eos_cb(self, bus, message):
        pass

    def bus_tag_cb(self, bus, message):
        pass

    def bus_error_cb(self, bus, message):
        exc = GstException(*message.parse_error())
        self.setAndRaiseException(exc)
        gst.debug('error, scheduling stop')
        #self.runner.schedule(0, self.stop)
