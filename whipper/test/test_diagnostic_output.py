"""Subprocess diagnostics remain available after parsing and decoding."""

import os
import unittest
from unittest import mock

from whipper.program import cdrdao, soxi


class CdrdaoDiagnosticsTestCase(unittest.TestCase):
    def test_consumed_stderr_is_in_missing_toc_error(self):
        task = cdrdao.ReadTOCTask('/dev/synthetic')
        os.close(task.fd)
        os.unlink(task.tocfile)
        task.schedule = mock.Mock()
        task.setProgress = mock.Mock()
        task.stop = mock.Mock()
        task.setAndRaiseException = mock.Mock()
        task._popen = mock.Mock(returncode=1)
        task._popen.recv_err.side_effect = [
            b'ERROR: cannot open device\n', b'bad byte: \xff\n', b'']
        task._popen.poll.return_value = 1
        task._read(None)
        self.assertEqual(task._buffer, '')
        task._read(None)
        self.assertEqual(task._buffer, '')
        task._read(None)
        error = task.setAndRaiseException.call_args[0][0]
        self.assertIsInstance(error, FileNotFoundError)
        self.assertIn('ERROR: cannot open device', str(error))
        self.assertIn('bad byte: \ufffd', str(error))
        self.assertIn('returncode=1', str(error))


class SoxiDiagnosticsTestCase(unittest.TestCase):
    def test_failed_decodes_stderr(self):
        task = soxi.AudioLengthTask('/synthetic.wav')
        task.readbyteserr(b'cannot read: \xff')
        task.readbyteserr(' tail')
        task.setException = mock.Mock()
        task.failed()
        self.assertEqual(str(task.setException.call_args[0][0]),
                         'soxi failed: cannot read: \ufffd tail')

    def test_done_decodes_stderr_and_reads_length(self):
        task = soxi.AudioLengthTask('/synthetic.wav')
        task.readbyteserr(b'warning: \xfe\n')
        task.readbytesout(b'5880\n')
        with self.assertLogs(soxi.logger, level='WARNING') as logs:
            task.done()
        self.assertEqual(task.length, 5880)
        self.assertIn('warning: \ufffd', logs.output[0])
