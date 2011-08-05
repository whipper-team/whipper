# -*- Mode: Python; test-case-name: test_taskgtk -*-
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

import gobject
import gtk

import task

class GtkProgressRunner(gtk.VBox, task.TaskRunner):
    """
    I am a widget that shows progress on a task.
    """

    __gsignals__ = {
        'stop': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, ())
    }

    def __init__(self):
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
        task.start(self)

    def schedule(self, delta, callable, *args, **kwargs):
        def c():
            callable(*args, **kwargs)
            return False
        gobject.timeout_add(int(delta * 1000L), c)

    def started(self, task):
        pass

    def stopped(self, task):
        self.emit('stop')
        # self._task.removeListener(self)

    def progressed(self, task, value):
        self._progress.set_fraction(value)

    def described(self, task, description):
        self._label.set_text(description)
