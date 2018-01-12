import os

from whipper.common import common
from whipper.common import task as ctask

import logging
logger = logging.getLogger(__name__)

SOXI = 'soxi'


class AudioLengthTask(ctask.PopenTask):
    """Calculate the length of a track in audio samples.

    :cvar logCategory:
    :vartype logCategory:
    :cvar description:
    :vartype description:
    :cvar length: length of the decoded audio file, in audio samples.
    :vartype length: int or None
    :ivar logName:
    :vartype logName:
    :ivar command:
    :vartype command:
    :ivar error:
    :vartype error:
    :ivar output:
    :vartype output:
    """

    logCategory = 'AudioLengthTask'
    description = 'Getting length of audio track'
    length = None

    def __init__(self, path):
        assert type(path) is unicode, "%r is not unicode" % path

        self.logName = os.path.basename(path).encode('utf-8')

        self.command = [SOXI, '-s', path]

        self._error = []
        self._output = []

    def commandMissing(self):
        raise common.MissingDependencyException('soxi')

    def readbytesout(self, bytes):
        self._output.append(bytes)

    def readbyteserr(self, bytes):
        self._error.append(bytes)

    def failed(self):
        self.setException(Exception("soxi failed: %s" % "".join(self._error)))

    def done(self):
        if self._error:
            logger.warning("soxi reported on stderr: %s", "".join(self._error))
        self.length = int("".join(self._output))
