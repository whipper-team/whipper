# -*- Mode: Python; test-case-name: morituri.test.test_header -*-
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

from morituri.common import task

class TaskProgress(gtk.VBox):
    __gsignals__ = {
        'stop': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, ())
    }

    def __init__(self, task):
        gtk.VBox.__init__(self)
        self.set_border_width(6)
        self.set_spacing(6)

        label = gtk.Label(task.description)
        self.add(label)

        self._progress = gtk.ProgressBar()
        self.add(self._progress)

        task.addListener(self)

    def start(self):
        pass

    def stop(self):
        self.emit('stop')

    def progress(self, value):
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

crctask = task.CRCTask(path, start, end)

window = gtk.Window()
progress = TaskProgress(crctask)
progress.connect('stop', lambda _: gtk.main_quit())
window.add(progress)
window.show_all()

crctask.start()

gtk.main()

print "CRC: %08X" % crctask.crc
