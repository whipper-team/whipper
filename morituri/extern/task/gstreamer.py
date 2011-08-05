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

import task

class GstException(Exception):
    def __init__(self, gerror, debug):
        self.args = (gerror, debug, )
        self.gerror = gerror
        self.debug = debug

    def __repr__(self):
        return '<GstException: GError %r, debug %r>' % (
            self.gerror.message, self.debug)

class GstPipelineTask(task.Task):
    """
    I am a base class for tasks that use a GStreamer pipeline.

    I handle errors and raise them appropriately.

    @cvar gst: the GStreamer module, so code does not have to import gst
               as a module in code everywhere to avoid option stealing.
    @var playing: whether the pipeline should be set to playing after
                  paused.  Some pipelines don't need to play for a task
                  to be done (for example, querying length)
    """

    gst = None
    playing = True

    ### task.Task implementations
    def start(self, runner):
        import gst
        self.gst = gst

        task.Task.start(self, runner)
        desc = self.getPipelineDesc()

        self.debug('creating pipeline %r', desc)
        self.pipeline = self.gst.parse_launch(desc)

        self._bus = self.pipeline.get_bus()
        self.gst.debug('got bus %r' % self._bus)

        # a signal watch calls callbacks from an idle loop
        # self._bus.add_signal_watch()

        # sync emission triggers sync-message signals which calls callbacks
        # from the thread that signals, but happens immediately
        self._bus.enable_sync_message_emission()
        self._bus.connect('sync-message::eos', self.bus_eos_cb)
        self._bus.connect('sync-message::tag', self.bus_tag_cb)
        self._bus.connect('sync-message::error', self.bus_error_cb)

        self.parsed()

        self.debug('setting pipeline to PAUSED')
        self.pipeline.set_state(gst.STATE_PAUSED)
        self.debug('set pipeline to PAUSED')
        # FIXME: this can block
        ret = self.pipeline.get_state()
        self.debug('got pipeline to PAUSED: %r', ret)

        if not self.exception:
            self.paused()
        else:
            raise self.exception

        self.play()

    def play(self):
        # since set_state returns non-False, adding it as timeout_add
        # will repeatedly call it, and block the main loop; so
        #   gobject.timeout_add(0L, self._pipeline.set_state,
        #       gst.STATE_PLAYING)
        # would not work.
        def playLater():
            if self.exception:
                self.debug('playLater: exception was raised, not playing')
                self.stop()
                return False

            self.debug('setting pipeline to PLAYING')
            self.pipeline.set_state(self.gst.STATE_PLAYING)
            self.debug('set pipeline to PLAYING')
            return False

        if self.playing:
            self.debug('scheduling setting pipeline to PLAYING')
            self.schedule(0, playLater)

    def stop(self):
        self.debug('stopping')
        self.debug('setting state to NULL')
        self.pipeline.set_state(self.gst.STATE_NULL)
        self.debug('set state to NULL')
        self.stopped()
        task.Task.stop(self)


    ### subclass required implementations
    def getPipelineDesc(self):
        """
        subclasses should implement this to provide a pipeline description.

        @rtype: str
        """
        raise NotImplementedError

    ### subclass optional implementations
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

    def stopped(self):
        """
        Called after pipeline is set back to NULL but before chaining up to
        stop()
        """
        pass

    def bus_eos_cb(self, bus, message):
        """
        Called synchronously (ie from messaging thread) on eos message.

        Override me to handle eos
        """
        pass

    def bus_tag_cb(self, bus, message):
        """
        Called synchronously (ie from messaging thread) on tag message.

        Override me to handle tags.
        """
        pass

    def bus_error_cb(self, bus, message):
        """
        Called synchronously (ie from messaging thread) on error message.
        """
        exc = GstException(*message.parse_error())
        self.setAndRaiseException(exc)
        self.debug('error, scheduling stop')
        self.schedule(0, self.stop)
