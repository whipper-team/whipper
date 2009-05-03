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
import gtk

from morituri.common import log

class Task(object, log.Loggable):
    """
    I wrap a task in an asynchronous interface.
    I can be listened to for starting, stopping, and progress updates.

    @ivar  description: what am I doing
    """
    description = 'I am doing something.'

    progress = 0.0
    increment = 0.01
    running = False
    runner = None

    _listeners = None


    ### subclass methods
    def start(self, runner):
        """
        Start the task.

        Subclasses should chain up to me at the beginning.
        """
        self.setProgress(self.progress)
        self.running = True
        self.runner = runner
        self._notifyListeners('started')

    def stop(self):
        """
        Stop the task.

        Subclasses should chain up to me at the end.
        """
        self.debug('stopping')
        self.running = False
        self.runner = None
        self._notifyListeners('stopped')

    ### base class methods
    def setProgress(self, value):
        """
        Notify about progress changes bigger than the increment.
        Called by subclass implementations as the task progresses.
        """
        if value - self.progress > self.increment or value >= 1.0 or value == 0.0:
            self.progress = value
            self._notifyListeners('progressed', value)
            self.log('notifying progress: %r', value)
        
    def setDescription(self, description):
        if description != self.description:
            self._notifyListeners('described', description)
            self.description = description

    def addListener(self, listener):
        """
        Add a listener for task status changes.

        Listeners should implement started, stopped, and progressed.
        """
        if not self._listeners:
            self._listeners = []
        self._listeners.append(listener)

    def _notifyListeners(self, methodName, *args, **kwargs):
            if self._listeners:
                for l in self._listeners:
                    getattr(l, methodName)(self, *args, **kwargs)

# this is a Dummy task that can be used if this works at all
class DummyTask(Task):
    def start(self, runner):
        Task.start(self, runner)
        self.runner.schedule(1.0, self._wind)

    def _wind(self):
        self.setProgress(min(self.progress + 0.1, 1.0))

        if self.progress >= 1.0:
            self.stop()
            return

        self.runner.schedule(1.0, self._wind)

class BaseMultiTask(Task):
    """
    I perform multiple tasks.
    """

    description = 'Doing various tasks'
    tasks = None

    def __init__(self):
        self.tasks = []
         
    def addTask(self, task):
        if self.tasks is None:
            self.tasks = []
        self.tasks.append(task)

    def start(self, runner):
        Task.start(self, runner)

        # initialize task tracking
        self._task = 0
        self.__tasks = self.tasks[:]
        self._generic = self.description

        self.next()

    def next(self):
        # start next task
        task = self.__tasks[0]
        del self.__tasks[0]
        self.debug('BaseMultiTask.next(): starting task %r', task)
        self._task += 1
        self.setDescription("%s (%d of %d) ..." % (
            self._generic, self._task, len(self.tasks)))
        task.addListener(self)
        task.start(self.runner)
        
    ### listener methods
    def started(self, task):
        pass

    def progressed(self, task, value):
        pass

    def stopped(self, task):
        if not self.__tasks:
            self.stop()
            return

        # pick another
        self.next()


class MultiTask(BaseMultiTask):
    """
    I perform multiple tasks.
    I track progress of each individual task, going back to 0 for each task.
    """

    def start(self, runner):
        self.debug('MultiTask.start()')
        BaseMultiTask.start(self, runner)

    def next(self):
        self.debug('MultiTask.next()')
        # start next task
        self.progress = 0.0 # reset progress for each task
        BaseMultiTask.next(self)
        
    ### listener methods
    def progressed(self, task, value):
        self.setProgress(value)

class MultiCombinedTask(BaseMultiTask):
    """
    I perform multiple tasks.
    I track progress as a combined progress on all tasks on task granularity.
    """

    _stopped = 0
       
    ### listener methods
    def progressed(self, task, value):
        self.setProgress(float(self._stopped + value) / len(self.tasks))

    def stopped(self, task):
        self._stopped += 1
        self.setProgress(float(self._stopped) / len(self.tasks))
        BaseMultiTask.stopped(self, task)

class TaskRunner(object):
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

    ### methods for tasks to call
    def schedule(self, delta, callable, *args, **kwargs):
        """
        Schedule a single future call.

        Subclasses should implement this.

        @type  delta: float
        @param delta: time in the future to schedule call for, in seconds.
        """
        raise NotImplementedError

    ### listener callbacks
    def progressed(self, task, value):
        """
        Implement me to be informed about progress.

        @type  value: float
        @param value: progress, from 0.0 to 1.0
        """

    def described(self, task, description):
        """
        Implement me to be informed about description changes.

        @type  description: str
        @param description: description
        """

    def started(self, task):
        """
        Implement me to be informed about the task starting.
        """

    def stopped(self, task):
        """
        Implement me to be informed about the task starting.
        """


class SyncRunner(TaskRunner):
    """
    I run the task synchronously in a gobject MainLoop.
    """
    def __init__(self, verbose=True):
        self._verbose = verbose

    def run(self, task, verbose=None, skip=False):
        self._task = task
        self._verboseRun = self._verbose
        if verbose is not None:
            self._verboseRun = verbose
        self._skip = skip

        self._loop = gobject.MainLoop()
        self._task.addListener(self)
        # only start the task after going into the mainloop,
        # otherwise the task might complete before we are in it
        gobject.timeout_add(0L, self._task.start, self)
        self._loop.run()

    def schedule(self, delta, callable, *args, **kwargs):
        def c():
            callable(*args, **kwargs)
            return False
        gobject.timeout_add(int(delta * 1000L), c)

    def progressed(self, task, value):
        if not self._verboseRun:
            return

        self._report()

        if value >= 1.0:
            if self._skip:
                sys.stdout.write('%s %3d %%\n' % (
                    self._task.description, 100.0))
            else:
                # clear with whitespace
                text = '%s %3d %%' % (
                    self._task.description, 100.0)
                sys.stdout.write("%s\r" % (' ' * len(text), ))

    def described(self, task, description):
        if self._verboseRun:
            self._report()

    def stopped(self, task):
        self._loop.quit()

    def _report(self):
        sys.stdout.write('%s %3d %%\r' % (
            self._task.description, self._task.progress * 100.0))
        sys.stdout.flush()

class GtkProgressRunner(gtk.VBox, TaskRunner):
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

if __name__ == '__main__':
    task = DummyTask()
    runner = SyncRunner()
    runner.run(task)
