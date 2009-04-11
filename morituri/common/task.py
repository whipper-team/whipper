# -*- Mode: Python; test-case-name: morituri.test.test_common_task -*-
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

import gobject

class Task(object):
    """
    I wrap a task in an asynchronous interface.
    I can be listened to for starting, stopping, and progress updates.

    @ivar  description: what am I doing
    """
    description = 'I am doing something.'

    progress = 0.0
    increment = 0.01
    running = False

    _listeners = None


    ### subclass methods
    def start(self):
        """
        Subclasses should chain up to me at the beginning.
        """
        self.progress = 0.0
        self.running = True
        self._notifyListeners('started')

    def stop(self):
        """
        Subclasses should chain up to me at the end.
        """
        self.debug('stopping')
        self.running = False
        self._notifyListeners('stopped')

    ### base class methods
    def debug(self, *args, **kwargs):
        return
        print self, args, kwargs
        sys.stdout.flush()

    def setProgress(self, value):
        if value - self.progress > self.increment or value >= 1.0:
            self.progress = value
            self._notifyListeners('progressed', value)
            self.debug('notifying progress', value)
        
    def addListener(self, listener):
        if not self._listeners:
            self._listeners = []
        self._listeners.append(listener)

    def _notifyListeners(self, methodName, *args, **kwargs):
            if self._listeners:
                for l in self._listeners:
                    getattr(l, methodName)(*args, **kwargs)

class TaskRunner:
    """
    I am a base class for task runners.
    Task runners should be reusable.
    """

    def run(self, task):
        """
        Run the given task.

        @type  task: Task
        """
        raise NotImplementedError

    # listener callbacks
    def progressed(self, value):
        """
        Implement me to be informed about progress.

        @type  value: float
        @param value: progress, from 0.0 to 1.0
        """

    def started(self):
        """
        Implement me to be informed about the task starting.
        """

    def stopped(self):
        """
        Implement me to be informed about the task starting.
        """

class SyncRunner(TaskRunner):
    def run(self, task):
        self._task = task
        self._loop = gobject.MainLoop()
        self._task.addListener(self)
        self._task.start()
        self._loop.run()

    def progressed(self, value):
        sys.stdout.write('%s %3d %%\r' % (
            self._task.description, value * 100.0))
        sys.stdout.flush()

        if value >= 1.0:
            sys.stdout.write('%s %3d %%\n' % (
                self._task.description, 100.0))

    def stopped(self):
        self._loop.quit()
