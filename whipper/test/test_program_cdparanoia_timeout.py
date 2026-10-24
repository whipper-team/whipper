"""Deterministic reader lifecycle tests without optical drives or sleeps."""

import heapq
import io
import os
import subprocess
import tempfile
import unittest
from unittest import mock

from whipper.common import common
from whipper.extern.task import task
from whipper.program import cdparanoia


class ClockRunner:
    """Advance a fake monotonic clock to each scheduled callback."""

    def __init__(self):
        self.now = 0.0
        self.calls = []
        self.handles = []
        self.stops = 0

    def schedule(self, reader, delay, callback, *args):
        handle = mock.Mock()
        handle.cancelled = False
        handle.cancel.side_effect = lambda: setattr(handle, 'cancelled', True)
        self.handles.append(handle)
        heapq.heappush(self.calls, (self.now + delay, len(self.handles),
                                    handle, callback, args))
        return handle

    def advance(self):
        when, _, handle, callback, args = heapq.heappop(self.calls)
        self.now = when
        if not handle.cancelled:
            callback(*args)

    def run(self, reader):
        reader.addListener(self)
        reader.start(self)
        steps = 0
        while reader.running:
            self.advance()
            steps += 1
            if steps > 10000:
                raise AssertionError('reader did not stop')

    def started(self, reader):
        pass

    def stopped(self, reader):
        self.stops += 1

    def progressed(self, reader, progress):
        pass


class SimulatedProcess:
    """Script stderr/output growth, exit, and signal responses on fake time."""

    def __init__(self, runner, path, events=(), end=None, code=0,
                 ignore_terminate=False, ignore_kill=False):
        self.runner = runner
        self.path = path
        self.events = list(events)
        self.end = end
        self.code = code
        self.ignore_terminate = ignore_terminate
        self.ignore_kill = ignore_kill
        self.returncode = None
        self.stdin = io.BytesIO()
        self.stdout = io.BytesIO()
        self.stderr = io.BytesIO()
        self.terminated = 0
        self.killed = 0
        self.waits = []
        self.reaped = False
        self.reads = 0

    def recv_err(self):
        self.reads += 1
        if self.events and self.events[0][0] <= self.runner.now:
            _, text, size = self.events.pop(0)
            if size is not None:
                with open(self.path, 'wb') as output:
                    output.truncate(size)
            return text
        return b''

    def poll(self):
        if self.end is not None and self.runner.now >= self.end:
            self.returncode = self.code
        return self.returncode

    def terminate(self):
        self.terminated += 1
        if not self.ignore_terminate:
            self.returncode = -15

    def kill(self):
        self.killed += 1
        if not self.ignore_kill:
            self.returncode = -9

    def wait(self, timeout=None):
        self.waits.append(timeout)
        if self.poll() is None:
            raise subprocess.TimeoutExpired('simulated cd-paranoia', timeout)
        self.reaped = True
        return self.returncode


class FakeTable:
    tracks = [object()]

    def getTrackStart(self, number):
        return 0


class ReadTimeoutTestCase(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = os.path.join(self.directory.name, 'track.wav')
        self.runner = ClockRunner()
        self.clock = mock.patch.object(cdparanoia.time, 'monotonic',
                                       side_effect=lambda: self.runner.now)
        self.clock.start()
        self.addCleanup(self.clock.stop)
        self.expected = 10 * common.BYTES_PER_FRAME + 44

    def reader(self, **kwargs):
        return cdparanoia.ReadTrackTask(self.path, FakeTable(), 0, 9,
                                        overread=False, **kwargs)

    def run_reader(self, process, **kwargs):
        reader = self.reader(**kwargs)
        with mock.patch.object(cdparanoia.asyncsub, 'Popen',
                               return_value=process):
            self.runner.run(reader)
        self.assertFalse(reader.running)
        self.assertIsNone(reader.runner)
        self.assertIsNone(reader._poll_handle)
        self.assertEqual(self.runner.stops, 1)
        self.assertTrue(process.stdin.closed)
        self.assertTrue(process.stdout.closed)
        self.assertTrue(process.stderr.closed)
        self.assertTrue(all(wait is not None for wait in process.waits))
        # Even a ready callback delivered after cancellation must do nothing.
        reads = process.reads
        reader._read(self.runner)
        self.assertEqual(process.reads, reads)
        return reader

    @staticmethod
    def progress(frame):
        return ('##: 0 [read] @ %d\n' %
                (frame * common.WORDS_PER_FRAME)).encode()

    def test_quiet_stall_expires_and_reaps(self):
        process = SimulatedProcess(self.runner, self.path)
        reader = self.run_reader(process, read_timeout=5, idle_timeout=1)
        self.assertIsInstance(reader.exception, cdparanoia.ReadTimeoutError)
        self.assertEqual(reader.exception.kind, 'inactivity')
        self.assertIn('1 seconds', str(reader.exception))
        self.assertAlmostEqual(self.runner.now, 1)
        self.assertEqual(process.terminated, 1)
        self.assertEqual(process.killed, 0)
        self.assertTrue(process.reaped)

    def test_repeated_or_backward_progress_and_chatter_do_not_reset_idle(self):
        events = [(0.1, self.progress(2), None),
                  (1.2, self.progress(2), None),
                  (1.4, self.progress(1), None),
                  (1.6, b'checking sector again\n', None)]
        process = SimulatedProcess(self.runner, self.path, events)
        reader = self.run_reader(process, read_timeout=10, idle_timeout=1)
        self.assertEqual(reader.exception.kind, 'inactivity')
        self.assertAlmostEqual(self.runner.now, 2)

    def test_slow_forward_progress_completes_beyond_idle_interval(self):
        events = [(1, self.progress(2), None),
                  (2, self.progress(4), None),
                  (3, self.progress(7), None),
                  (4, self.progress(10), self.expected)]
        process = SimulatedProcess(self.runner, self.path, events, end=4)
        reader = self.run_reader(process, read_timeout=10, idle_timeout=1.5)
        self.assertIsNone(reader.exception)
        self.assertGreater(reader.duration, 1.5)
        self.assertTrue(process.reaped)
        self.assertEqual(process.terminated, 0)

    def test_file_growth_counts_as_progress_without_stderr(self):
        events = [(1, b'', 100), (2, b'', 200),
                  (3, self.progress(10), self.expected)]
        process = SimulatedProcess(self.runner, self.path, events, end=3)
        reader = self.run_reader(process, read_timeout=10, idle_timeout=1.5)
        self.assertIsNone(reader.exception)
        self.assertTrue(os.path.exists(self.path))  # caller owns output

    def test_hard_limit_bounds_continuous_forward_progress(self):
        events = [(1, self.progress(2), 100),
                  (2, self.progress(4), 200),
                  (3, self.progress(6), 300)]
        process = SimulatedProcess(self.runner, self.path, events)
        reader = self.run_reader(process, read_timeout=3, idle_timeout=1.5)
        self.assertEqual(reader.exception.kind, 'elapsed time')
        self.assertAlmostEqual(self.runner.now, 3)
        self.assertTrue(os.path.exists(self.path))

    def test_progress_past_read_span_does_not_extend_idle(self):
        events = [(1, self.progress(11), None),
                  (1.2, self.progress(12), None),
                  (1.4, self.progress(13), None)]
        process = SimulatedProcess(self.runner, self.path, events)
        reader = self.run_reader(process, idle_timeout=1)
        self.assertEqual(reader.exception.kind, 'inactivity')
        self.assertAlmostEqual(self.runner.now, 2)

    def test_short_limit_applies_before_initial_poll(self):
        process = SimulatedProcess(self.runner, self.path)
        self.run_reader(process, read_timeout=0.1)
        self.assertAlmostEqual(self.runner.now, 0.1)

    def test_exit_observed_at_deadline_succeeds(self):
        process = SimulatedProcess(
            self.runner, self.path,
            [(1, self.progress(10), self.expected)], end=1)
        reader = self.run_reader(process, read_timeout=1, idle_timeout=1)
        self.assertIsNone(reader.exception)
        self.assertEqual(process.terminated, 0)

    def test_nonzero_exit_closes_and_reaps(self):
        process = SimulatedProcess(
            self.runner, self.path,
            [(1, self.progress(10), self.expected)], end=1, code=7)
        reader = self.run_reader(process, read_timeout=5, idle_timeout=2)
        self.assertIsInstance(reader.exception, cdparanoia.ReturnCodeError)
        self.assertEqual(reader.exception.returncode, 7)
        self.assertTrue(process.reaped)

    def test_missing_and_partial_output_fail_with_cleanup(self):
        for size in (None, 200):
            with self.subTest(size=size):
                self.runner = ClockRunner()
                process = SimulatedProcess(self.runner, self.path,
                                           [(1, b'', size)], end=1, code=1)
                reader = self.run_reader(process, read_timeout=5)
                self.assertIsNotNone(reader.exception)
                self.assertTrue(process.reaped)

    def test_terminate_resistant_process_is_killed_and_reaped(self):
        process = SimulatedProcess(self.runner, self.path,
                                   ignore_terminate=True)
        reader = self.run_reader(process, idle_timeout=1)
        self.assertIsInstance(reader.exception, cdparanoia.ReadTimeoutError)
        self.assertEqual(process.killed, 1)
        self.assertTrue(process.reaped)
        self.assertEqual(process.waits, [2, 2])

    def test_unkillable_process_reports_fatal_cleanup_failure(self):
        process = SimulatedProcess(self.runner, self.path,
                                   ignore_terminate=True, ignore_kill=True)
        reader = self.run_reader(process, idle_timeout=1)
        self.assertIsInstance(reader.exception, cdparanoia.ReadCleanupError)
        self.assertIn('could not be reaped', str(reader.exception))
        self.assertFalse(process.reaped)
        self.assertEqual(process.waits, [2, 2])

    def test_external_stop_cancels_pending_poll(self):
        process = SimulatedProcess(self.runner, self.path)
        reader = self.reader(read_timeout=5)
        reader.addListener(self.runner)
        with mock.patch.object(cdparanoia.asyncsub, 'Popen',
                               return_value=process):
            reader.start(self.runner)
        handle = reader._poll_handle
        reader.stop()
        self.assertTrue(handle.cancelled)
        self.runner.advance()
        self.assertEqual(process.reads, 0)
        self.assertTrue(process.reaped)

    def test_ordinary_reads_have_no_timeout(self):
        process = SimulatedProcess(
            self.runner, self.path,
            [(15, self.progress(10), self.expected)], end=15)
        reader = self.run_reader(process)
        self.assertIsNone(reader.exception)
        self.assertGreaterEqual(reader.duration, 15)
        self.assertEqual(process.terminated, 0)

    def test_invalid_timeouts_are_rejected(self):
        for name in ('read_timeout', 'idle_timeout'):
            for value in (0, -1, float('inf'), float('nan')):
                with self.subTest(name=name, value=value):
                    with self.assertRaises(ValueError):
                        self.reader(**{name: value})

    def test_real_runner_returns_cancellable_poll_handle(self):
        runner = task.SyncRunner(verbose=False)
        import asyncio
        runner._loop = asyncio.new_event_loop()
        self.addCleanup(runner._loop.close)
        reader = task.Task()
        reader.runner = runner
        handle = reader.schedule(1, lambda: None)
        handle.cancel()
        self.assertTrue(handle.cancelled())
