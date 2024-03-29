# -*- Mode: Python -*-
# vi:si:et:sw=4:sts=4:ts=4

# Copyright (C) 2009 Thomas Vander Stichele

# This file is part of whipper.
#
# whipper is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# whipper is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with whipper.  If not, see <http://www.gnu.org/licenses/>.

import asyncio
import logging
import sys

logger = logging.getLogger(__name__)


class TaskException(Exception):
    """Wrap an exception that happened during task execution."""

    exception = None  # original exception

    def __init__(self, exception, message=None):
        self.exception = exception
        self.exceptionMessage = message
        self.args = (exception, message, )

# lifted from flumotion log module


def _getExceptionMessage(exception, frame=-1, filename=None):
    """
    Return a short message based on an exception, useful for debugging.

    Tries to find where the exception was triggered.
    """
    import traceback

    stack = traceback.extract_tb(sys.exc_info()[2])
    if filename:
        stack = [f for f in stack if f[0].find(filename) > -1]

    # badly raised exceptions can come without a stack
    if stack:
        (filename, line, func, text) = stack[frame]
    else:
        (filename, line, func, text) = ('no stack', 0, 'none', '')

    exc = exception.__class__.__name__
    msg = ""
    # a shortcut to extract a useful message out of most exceptions
    # for now
    if str(exception):
        msg = ": %s" % str(exception)
    return "exception %(exc)s at %(filename)s:%(line)s: %(func)s()%(msg)s" \
        % locals()


class LogStub:
    """Stub for a log interface."""

    @staticmethod
    def log(message, *args):
        logger.info(message, *args)

    @staticmethod
    def debug(message, *args):
        logger.debug(message, *args)

    @staticmethod
    def warning(message, *args):
        logger.warning(message, *args)


class Task(LogStub):
    """
    Wrap a task in an asynchronous interface.

    Can be listened to for starting, stopping, description changes
    and progress updates.

    I communicate an error by setting self.exception to an exception and
    stopping myself from running.
    The listener can then handle the Task.exception.

    :cvar description: what am I doing
    :cvar exception: set if an exception happened during the task
                     execution. Will be raised through ``run()`` at the end
    """

    logCategory = 'Task'

    description = 'I am doing something.'

    progress = 0.0
    increment = 0.01
    running = False
    runner = None
    exception = None
    exceptionMessage = None
    exceptionTraceback = None

    _listeners = None

    # subclass methods
    def start(self, runner):
        """
        Start the task.

        Subclasses should chain up to me at the beginning.

        Subclass implementations should raise exceptions immediately in
        case of failure (using set(AndRaise)Exception) first, or do it later
        using those methods.

        If start doesn't raise an exception, the task should run until
        complete, or ``setException()`` and ``stop()``.
        """
        self.debug('starting')
        self.setProgress(self.progress)
        self.running = True
        self.runner = runner
        self._notifyListeners('started')

    def stop(self):
        """
        Stop the task.

        Also resets the runner on the task.

        Subclasses should chain up to me at the end.
        It is important that they do so in all cases, even when
        they ran into an exception of their own.

        Listeners will get notified that the task is stopped,
        whether successfully or with an exception.
        """
        self.debug('stopping')
        self.running = False
        if not self.runner:
            print('ERROR: stopping task which is already stopped')
            import traceback
            traceback.print_stack()
        self.runner = None
        self.debug('reset runner to None')
        self._notifyListeners('stopped')

    # base class methods
    def setProgress(self, value):
        """
        Notify about progress changes bigger than the increment.

        Called by subclass implementations as the task progresses.
        """
        if (value - self.progress > self.increment or
                value >= 1.0 or value == 0.0):
            self.progress = value
            self._notifyListeners('progressed', value)
            self.debug('notifying progress: %r on %r',
                       value, self.description)

    def setDescription(self, description):
        if description != self.description:
            self._notifyListeners('described', description)
            self.description = description

    # FIXME: unify?
    def setExceptionAndTraceback(self, exception):
        """
        Call this to set a synthetically created exception.

        Not one that was actually raised and caught.
        """
        import traceback

        stack = traceback.extract_stack()[:-1]
        (filename, line, func, text) = stack[-1]
        exc = exception.__class__.__name__
        msg = ""
        # a shortcut to extract a useful message out of most exceptions
        # for now
        if str(exception):
            msg = ": %s" % str(exception)
        line = ("exception %(exc)s at %(filename)s:%(line)s: "
                "%(func)s()%(msg)s" % locals())

        self.exception = exception
        self.exceptionMessage = line
        self.exceptionTraceback = traceback.format_exc()
        self.debug('set exception, %r' % self.exceptionMessage)
    # FIXME: remove
    setAndRaiseException = setExceptionAndTraceback

    def setException(self, exception):
        """Call this to set a caught exception on the task."""
        import traceback

        self.exception = exception
        self.exceptionMessage = _getExceptionMessage(exception)
        self.exceptionTraceback = traceback.format_exc()
        self.debug('set exception, %r, %r' % (
            exception, self.exceptionMessage))

    def schedule(self, delta, callable_task, *args, **kwargs):
        if not self.runner:
            print("ERROR: scheduling on a task that's altready stopped")
            import traceback
            traceback.print_stack()
            return
        self.runner.schedule(self, delta, callable_task, *args, **kwargs)

    def addListener(self, listener):
        """
        Add a listener for task status changes.

        Listeners should implement started, stopped, and progressed.
        """
        self.debug('Adding listener %r', listener)
        if not self._listeners:
            self._listeners = []
        self._listeners.append(listener)

    def _notifyListeners(self, methodName, *args, **kwargs):
        if self._listeners:
            for listener in self._listeners:
                method = getattr(listener, methodName)
                try:
                    method(self, *args, **kwargs)
                # FIXME: catching too general exception (Exception)
                except Exception as e:
                    self.setException(e)


# FIXME: should this become a real interface, like in zope ?
class ITaskListener:
    """An interface for objects listening to tasks."""
    # listener callbacks

    def progressed(self, task, value):
        """
        Implement me to be informed about progress.

        :param task: a task
        :type task: Task
        :param value: progress, from 0.0 to 1.0
        :type value: float
        """

    def described(self, task, description):
        """
        Implement me to be informed about description changes.

        :param task: a task
        :type task: Task
        :param description: description
        :type description: str
        """

    def started(self, task):
        """Implement me to be informed about the task starting."""

    def stopped(self, task):
        """
        Implement me to be informed about the task stopping.

        If the task had an error, task.exception will be set.
        """


# this is a Dummy task that can be used to test if this works at all
class DummyTask(Task):
    def start(self, runner):
        Task.start(self, runner)
        self.schedule(1.0, self._wind)

    def _wind(self):
        self.setProgress(min(self.progress + 0.1, 1.0))

        if self.progress >= 1.0:
            self.stop()
            return

        self.schedule(1.0, self._wind)


class BaseMultiTask(Task, ITaskListener):
    """
    I perform multiple tasks.

    :cvar tasks: the tasks to run
    :vartype tasks: list(Task)
    """

    description = 'Doing various tasks'
    tasks = None

    def __init__(self):
        self.tasks = []
        self._task = 0

    def addTask(self, task):
        """
        Add a task.

        :type task: Task
        """
        if self.tasks is None:
            self.tasks = []
        self.tasks.append(task)

    def start(self, runner):
        """
        Start tasks.

        Tasks can still be added while running. For example,
        a first task can determine how many additional tasks to run.
        """
        Task.start(self, runner)

        # initialize task tracking
        if not self.tasks:
            self.warning('no tasks')
        self._generic = self.description

        self.next()

    def next(self):
        """Start the next task."""
        try:
            # start next task
            task = self.tasks[self._task]
            self._task += 1
            self.debug('BaseMultiTask.next(): starting task %d of %d: %r',
                       self._task, len(self.tasks), task)
            self.setDescription("%s (%d of %d) ..." % (
                task.description, self._task, len(self.tasks)))
            task.addListener(self)
            task.start(self.runner)
            self.debug('BaseMultiTask.next(): started task %d of %d: %r',
                       self._task, len(self.tasks), task)
        # FIXME: catching too general exception (Exception)
        except Exception as e:
            self.setException(e)
            self.debug('Got exception during next: %r', self.exceptionMessage)
            self.stop()
            return

    # ITaskListener methods
    def started(self, task):
        pass

    def progressed(self, task, value):
        pass

    def stopped(self, task):  # noqa: D401
        """
        Subclasses should chain up to me at the end of their implementation.

        They should fall through to chaining up if there is an exception.
        """
        self.debug('BaseMultiTask.stopped: task %r (%d of %d)',
                   task, self.tasks.index(task) + 1, len(self.tasks))
        if task.exception:
            self.warning('BaseMultiTask.stopped: exception %r',
                         task.exceptionMessage)
            self.exception = task.exception
            self.exceptionMessage = task.exceptionMessage
            self.stop()
            return

        if self._task == len(self.tasks):
            self.debug('BaseMultiTask.stopped: all tasks done')
            self.stop()
            return

        # pick another
        self.debug('BaseMultiTask.stopped: pick next task')
        self.schedule(0, self.next)


class MultiSeparateTask(BaseMultiTask):
    """
    Perform multiple tasks.

    Track progress of each individual task, going back to 0 for each task.
    """

    description = 'Doing various tasks separately'

    def start(self, runner):
        self.debug('MultiSeparateTask.start()')
        BaseMultiTask.start(self, runner)

    def next(self):
        self.debug('MultiSeparateTask.next()')
        # start next task
        self.progress = 0.0  # reset progress for each task
        BaseMultiTask.next(self)

    # ITaskListener methods
    def progressed(self, task, value):
        self.setProgress(value)

    def described(self, description):
        self.setDescription("%s (%d of %d) ..." % (
            description, self._task, len(self.tasks)))


class MultiCombinedTask(BaseMultiTask):
    """
    Perform multiple tasks.

    Track progress as a combined progress on all tasks on task granularity.
    """

    description = 'Doing various tasks combined'
    _stopped = 0

    # ITaskListener methods
    def progressed(self, task, value):
        self.setProgress(float(self._stopped + value) / len(self.tasks))

    def stopped(self, task):
        self._stopped += 1
        self.setProgress(float(self._stopped) / len(self.tasks))
        BaseMultiTask.stopped(self, task)


class TaskRunner(LogStub):
    """
    Base class for task runners.

    Task runners should be reusable.
    """

    logCategory = 'TaskRunner'

    def run(self, task):
        """
        Run the given task.

        :type task: Task
        """
        raise NotImplementedError

    # methods for tasks to call
    def schedule(self, delta, callable_task, *args, **kwargs):
        """
        Schedule a single future call.

        Subclasses should implement this.

        :param delta: time in the future to schedule call for, in seconds.
        :type delta: float
        :param callable_task: a task
        :type callable_task: Task
        """
        raise NotImplementedError


class SyncRunner(TaskRunner, ITaskListener):
    """Run the task synchronously in an asyncio event loop."""

    def __init__(self, verbose=True):
        self._verbose = verbose
        self._longest = 0  # longest string shown; for clearing

    def run(self, task, verbose=None, skip=False):
        self.debug('run task %r', task)
        self._task = task
        self._verboseRun = self._verbose
        if verbose is not None:
            self._verboseRun = verbose
        self._skip = skip

        self._loop = asyncio.new_event_loop()
        self._task.addListener(self)
        # only start the task after going into the mainloop,
        # otherwise the task might complete before we are in it
        self._loop.call_soon(self._startWrap, self._task)
        self.debug('run loop')
        self._loop.run_forever()

        self.debug('done running task %r', task)
        if task.exception:
            # catch the exception message
            # FIXME: this gave a traceback in the logging module
            self.debug('raising TaskException for %r, %r' % (
                task.exceptionMessage, task.exceptionTraceback))
            msg = task.exceptionMessage
            if task.exceptionTraceback:
                msg += "\n" + task.exceptionTraceback
            raise TaskException(task.exception, message=msg)

    def _startWrap(self, task):
        # wrap task start such that we can report any exceptions and
        # never hang
        try:
            self.debug('start task %r' % task)
            task.start(self)
        # FIXME: catching too general exception (Exception)
        except Exception as e:
            # getExceptionMessage uses global exception state that doesn't
            # hang around, so store the message
            task.setException(e)
            self.debug('exception during start: %r', task.exceptionMessage)
            self.stopped(task)

    def schedule(self, task, delta, callable_task, *args, **kwargs):
        def c():
            try:
                callable_task(*args, **kwargs)
                return False
            except Exception as e:
                self.debug('exception when calling scheduled callable %r',
                           callable_task)
                task.setException(e)
                self.stopped(task)
                raise

        self._loop.call_later(delta, c)

    # ITaskListener methods
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
                print(("%s\r" % (' ' * self._longest, )), end='')

    def _output(self, what, newline=False, ret=True):
        print(what, end='')
        print((' ' * (self._longest - len(what))), end='')
        if ret:
            print('\r', end='')
        if newline:
            print('')
        sys.stdout.flush()
        if len(what) > self._longest:
            self._longest = len(what)

    def described(self, task, description):
        if self._verboseRun:
            self._report()

    def stopped(self, task):
        self.debug('stopped task %r', task)
        self.progressed(task, 1.0)
        self._loop.stop()

    def _report(self):
        self._output('%s %3d %%' % (
            self._task.description, self._task.progress * 100.0))


if __name__ == '__main__':
    task = DummyTask()
    runner = SyncRunner()
    runner.run(task)
