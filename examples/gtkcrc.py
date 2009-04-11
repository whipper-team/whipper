# -*- Mode: Python -*-
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

import sys

import gst
import time

import gobject
gobject.threads_init()

import gtk

from morituri.common import task, crc

class TaskProgress(gtk.VBox, task.TaskRunner):
    __gsignals__ = {
        'stop': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, ())
    }

    def __init__(self):
        gst.info('__init__')
        gtk.VBox.__init__(self)
        self.set_border_width(6)
        self.set_spacing(6)

        self._label = gtk.Label()
        self.add(self._label)

        self._progress = gtk.ProgressBar()
        self.add(self._progress)

    def run(self, task):
        self._task = task
        self._label.set_text(task.description)
        task.addListener(self)
        while gtk.events_pending():
            gtk.main_iteration()
        task.start()

    def started(self):
        pass

    def stopped(self):
        self.emit('stop')
        # self._task.removeListener(self)

    def progressed(self, value):
        gst.info('progressed')
        # FIXME: why is this not painting the progress bar ?
        self._progress.set_fraction(value)


path = 'test.flac'

start = 0
end = -1
try:
    path = sys.argv[1]
except IndexError:
    pass

try:
    start = int(sys.argv[2])
except:
    pass

try:
    end = int(sys.argv[3])
except:
    pass

crctask = crc.CRC32Task(path, start, end)

# this is a Dummy task that can be used if this works at all
class DummyTask(task.Task):
    def start(self):
        task.Task.start(self)
        gobject.timeout_add(1000L, self._wind)

    def _wind(self):
        self.setProgress(min(self.progress + 0.1, 1.0))

        if self.progress >= 1.0:
            self.stop()
            return

        gobject.timeout_add(1000L, self._wind)

#crctask = DummyTask()

window = gtk.Window()
progress = TaskProgress()
progress.connect('stop', lambda _: gtk.main_quit())
window.add(progress)
window.show_all()

progress.run(crctask)

gtk.main()

print "CRC: %08X" % crctask.crc
