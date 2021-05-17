import os

from whipper.common import common
from whipper.common import task as ctask

import logging
logger = logging.getLogger(__name__)

SOXI = 'soxi'


class AudioLengthTask(ctask.PopenTask):
    """
    Calculate the length of a track in audio samples.

    :cvar length: length of the decoded audio file, in audio samples
    :vartype length: int
    """

    logCategory = 'AudioLengthTask'
    description = 'Getting length of audio track'
    length = None

    def __init__(self, path):
        """
        Init AudioLengthTask.

        :param path: path to audio track
        :type path: str
        """
        assert isinstance(path, str), "%r is not str" % path

        self.logName = os.path.basename(path)

        self.command = [SOXI, '-s', path]

        self._error = []
        self._output = []

    def commandMissing(self):
        raise common.MissingDependencyException('soxi')

    def readbytesout(self, bytes_stdout):
        self._output.append(bytes_stdout)

    def readbyteserr(self, bytes_stderr):
        self._error.append(bytes_stderr)

    def failed(self):
        self.setException(Exception("soxi failed: %s" % "".join(self._error)))

    def done(self):
        if self._error:
            logger.warning("soxi reported on stderr: %s", "".join(self._error))
        self.length = int("".join(o.decode() for o in self._output))
