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

from morituri.common import log

class Task(object, log.Loggable):
    """
    I wrap a task in an asynchronous interface.
    I can be listened to for starting, stopping, and progress updates.

    @ivar  description: what am I doing
    @ivar  exception:   set if an exception happened during the task
                        execution.
    """
    description = 'I am doing something.'

    progress = 0.0
    increment = 0.01
    running = False
    runner = None
    exception = None

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

    @ivar tasks: the tasks to run
    @type tasks: list of L{Task}
    """

    description = 'Doing various tasks'
    tasks = None

    def __init__(self):
        self.tasks = []
        self._task = 0
         
    def addTask(self, task):
        """
        Add a task.

        @type task: L{Task}
        """
        if self.tasks is None:
            self.tasks = []
        self.tasks.append(task)

    def start(self, runner):
        """
        Start tasks.

        Tasks can still be added while running.  For example,
        a first task can determine how many additional tasks to run.
        """
        Task.start(self, runner)

        # initialize task tracking
        if not self.tasks:
            self.warning('no tasks')
        self._generic = self.description

        self.next()

    def next(self):
        """
        Start the next task.
        """
        try:
            # start next task
            task = self.tasks[self._task]
            self._task += 1
            self.debug('BaseMultiTask.next(): starting task %r', task)
            self.setDescription("%s (%d of %d) ..." % (
                task.description, self._task, len(self.tasks)))
            task.addListener(self)
            task.start(self.runner)
        except Exception, e:
            self.debug('Got exception during next: %r',
                log.getExceptionMessage(e))
            self.exception = e
            self.stop()
            return
        
    ### listener methods
    def started(self, task):
        pass

    def progressed(self, task, value):
        pass

    def stopped(self, task):
        if task.exception:
            self.exception = task.exception
            self.stop()
            return

        if self._task == len(self.tasks):
            self.stop()
            return

        # pick another
        self.next()


class MultiSeparateTask(BaseMultiTask):
    """
    I perform multiple tasks.
    I track progress of each individual task, going back to 0 for each task.
    """
    description = 'Doing various tasks separately'

    def start(self, runner):
        self.debug('MultiSeparateTask.start()')
        BaseMultiTask.start(self, runner)

    def next(self):
        self.debug('MultiSeparateTask.next()')
        # start next task
        self.progress = 0.0 # reset progress for each task
        BaseMultiTask.next(self)
        
    ### listener methods
    def progressed(self, task, value):
        self.setProgress(value)

    def described(self, description):
        self.setDescription("%s (%d of %d) ..." % (
            description, self._task, len(self.tasks)))

class MultiCombinedTask(BaseMultiTask):
    """
    I perform multiple tasks.
    I track progress as a combined progress on all tasks on task granularity.
    """

    description = 'Doing various tasks combined'
    _stopped = 0
       
    ### listener methods
    def progressed(self, task, value):
        self.setProgress(float(self._stopped + value) / len(self.tasks))

    def stopped(self, task):
        self._stopped += 1
        self.setProgress(float(self._stopped) / len(self.tasks))
        BaseMultiTask.stopped(self, task)

class TaskRunner(object, log.Loggable):
    """
    I am a base class for task runners.
    Task runners should be reusable.
    """
    logCategory = 'TaskRunner'

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
        self._longest = 0 # longest string shown; for clearing

    def run(self, task, verbose=None, skip=False):
        self.debug('run task %r', task)
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

        self.debug('done running task %r', task)
        if task.exception:
            # FIXME: this gave a traceback in the logging module
            #self.debug('raising exception, %r',
            #    log.getExceptionMessage(self._task.exception))
            raise task.exception

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
                self._output('%s %3d %%' % (
                    self._task.description, 100.0))
            else:
                # clear with whitespace
                sys.stdout.write("%s\r" % (' ' * self._longest, ))

    def _output(self, what, newline=False, ret=True):
        sys.stdout.write(what)
        sys.stdout.write(' ' * (self._longest - len(what)))
        if ret:
            sys.stdout.write('\r')
        if newline:
            sys.stdout.write('\n')
        sys.stdout.flush()
        if len(what) > self._longest:
            #print; print 'setting longest', self._longest; print
            self._longest = len(what)

    def described(self, task, description):
        if self._verboseRun:
            self._report()

    def stopped(self, task):
        self.debug('stopped task %r', task)
        self.progressed(task, 1.0)
        self._loop.quit()

    def _report(self):
        self._output('%s %3d %%' % (
            self._task.description, self._task.progress * 100.0))

if __name__ == '__main__':
    task = DummyTask()
    runner = SyncRunner()
    runner.run(task)
