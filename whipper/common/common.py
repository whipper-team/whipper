# -*- Mode: Python; test-case-name: whipper.test.test_common_common -*-
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


import os
import os.path
import math
import subprocess

from whipper.extern import asyncsub

import logging
logger = logging.getLogger(__name__)

FRAMES_PER_SECOND = 75

SAMPLES_PER_FRAME = 588  # a sample is 2 16-bit values, left and right channel
WORDS_PER_FRAME = SAMPLES_PER_FRAME * 2
BYTES_PER_FRAME = SAMPLES_PER_FRAME * 4


class EjectError(SystemError):
    """Possibly ejects the drive in command.main.

    ivar args: is a tuple used by BaseException.__str__.
    :vartype args:
    ivar: device is the device path to eject.
    :vartype device:
    """

    def __init__(self, device, *args):
        self.args = args
        self.device = device


def msfToFrames(msf):
    """Convert a string value in MM:SS:FF to frames.

    :param msf: the MM:SS:FF value to convert.
    :type msf: str
    :returns: number of frames.
    :rtype: int
    """
    if ':' not in msf:
        return int(msf)

    m, s, f = msf.split(':')

    return 60 * FRAMES_PER_SECOND * int(m) \
        + FRAMES_PER_SECOND * int(s) \
        + int(f)


def framesToMSF(frames, frameDelimiter=':'):
    f = frames % FRAMES_PER_SECOND
    frames -= f
    s = (frames / FRAMES_PER_SECOND) % 60
    frames -= s * 60
    m = frames / FRAMES_PER_SECOND / 60

    return "%02d:%02d%s%02d" % (m, s, frameDelimiter, f)


def framesToHMSF(frames):
    # cdparanoia style
    f = frames % FRAMES_PER_SECOND
    frames -= f
    s = (frames / FRAMES_PER_SECOND) % 60
    frames -= s * FRAMES_PER_SECOND
    m = (frames / FRAMES_PER_SECOND / 60) % 60
    frames -= m * FRAMES_PER_SECOND * 60
    h = frames / FRAMES_PER_SECOND / 60 / 60

    return "%02d:%02d:%02d.%02d" % (h, m, s, f)


def formatTime(seconds, fractional=3):
    """Nicely format time in a human-readable format, like HH:MM:SS.mmm.

    If fractional is zero, no seconds will be shown.
    If it is greater than 0, we will show seconds and fractions of seconds.
    As a side consequence, there is no way to show seconds without fractions.

    :param seconds: the time in seconds to format.
    :type seconds: int or float
    :param fractional: how many digits to show for the fractional part of
                       seconds. (Default value = 3)
    :type fractional: int
    :returns: a nicely formatted time string.
    :rtype: str
    """
    chunks = []

    if seconds < 0:
        chunks.append(('-'))
        seconds = -seconds

    hour = 60 * 60
    hours = seconds / hour
    seconds %= hour

    minute = 60
    minutes = seconds / minute
    seconds %= minute

    chunk = '%02d:%02d' % (hours, minutes)
    if fractional > 0:
        chunk += ':%0*.*f' % (fractional + 3, fractional, seconds)

    chunks.append(chunk)

    return " ".join(chunks)


class MissingDependencyException(Exception):
    dependency = None

    def __init__(self, *args):
        self.args = args
        self.dependency = args[0]


class EmptyError(Exception):
    pass


class MissingFrames(Exception):
    """Less frames decoded than expected."""

    pass


def shrinkPath(path):
    """Shrink a full path to a shorter version.

    Used to handle ENAMETOOLONG

    :param path:
    :type path:
    """
    parts = list(os.path.split(path))
    length = len(parts[-1])
    target = 127
    if length <= target:
        target = pow(2, int(math.log(length, 2))) - 1

    name, ext = os.path.splitext(parts[-1])
    target -= len(ext) + 1

    # split on space, then reassemble
    words = name.split(' ')
    length = 0
    pieces = []
    for word in words:
        if length + 1 + len(word) <= target:
            pieces.append(word)
            length += 1 + len(word)
        else:
            break

    name = " ".join(pieces)
    # ext includes period
    parts[-1] = u'%s%s' % (name, ext)
    path = os.path.join(*parts)
    return path


def getRealPath(refPath, filePath):
    """Translate a .cue or .toc's FILE argument to an existing path.

    Does Windows path translation.
    Will look for the given file name, but with .flac and .wav as extensions.

    :param refPath: path to the file from which the track is referenced;
                    for example, path to the .cue file in the same directory
    :type refPath: unicode
    :param filePath:
    :type filePath: unicode
    """
    assert type(filePath) is unicode, "%r is not unicode" % filePath

    if os.path.exists(filePath):
        return filePath

    candidatePaths = []

    # .cue FILE statements can have Windows-style path separators, so convert
    # them as one possible candidate
    # on the other hand, the file may indeed contain a backslash in the name
    # on linux
    # FIXME: I guess we might do all possible combinations of splitting or
    #        keeping the slash, but let's just assume it's either Windows
    #        or linux
    # See https://thomas.apestaart.org/morituri/trac/ticket/107
    parts = filePath.split('\\')
    if parts[0] == '':
        parts[0] = os.path.sep
    tpath = os.path.join(*parts)

    for path in [filePath, tpath]:
        if path == os.path.abspath(path):
            candidatePaths.append(path)
        else:
            # if the path is relative:
            # - check relatively to the cue file
            # - check only the filename part relative to the cue file
            candidatePaths.append(os.path.join(
                os.path.dirname(refPath), path))
            candidatePaths.append(os.path.join(
                os.path.dirname(refPath), os.path.basename(path)))

    # Now look for .wav and .flac files, as .flac files are often named .wav
    for candidate in candidatePaths:
        noext, _ = os.path.splitext(candidate)
        for ext in ['wav', 'flac']:
            cpath = '%s.%s' % (noext, ext)
            if os.path.exists(cpath):
                return cpath

    raise KeyError("Cannot find file for %r" % filePath)


def getRelativePath(targetPath, collectionPath):
    """Get a relative path from the directory of collectionPath to targetPath.

    Used to determine the path to use in .cue/.m3u files

    :param targetPath:
    :type targetPath:
    :param collectionPath:
    :type collectionPath:
    """
    logger.debug('getRelativePath: target %r, collection %r' % (
        targetPath, collectionPath))

    targetDir = os.path.dirname(targetPath)
    collectionDir = os.path.dirname(collectionPath)
    if targetDir == collectionDir:
        logger.debug('getRelativePath: target and collection in same dir')
        return os.path.basename(targetPath)
    else:
        rel = os.path.relpath(
            targetDir + os.path.sep,
            collectionDir + os.path.sep)
        logger.debug(
            'getRelativePath: target and collection in different dir, %r' % rel
        )
        return os.path.join(rel, os.path.basename(targetPath))


class VersionGetter(object):
    """I get the version of a program by looking for it in command output.

    (Through a RegExp).

    :ivar dependency: name of the dependency providing the program
    :vartype dependency:
    :ivar args: the arguments to invoke to show the version
    :vartype args: list of str
    :ivar regexp: the regular expression to get the version
    :vartype regexp:
    :ivar expander: the expansion string for the version using the
                     regexp group dict
    :vartype expander:
    """

    def __init__(self, dependency, args, regexp, expander):
        self._dep = dependency
        self._args = args
        self._regexp = regexp
        self._expander = expander

    def get(self):
        version = "(Unknown)"

        try:
            p = asyncsub.Popen(self._args,
                               stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, close_fds=True)
            p.wait()
            output = asyncsub.recv_some(p, e=0, stderr=1)
            vre = self._regexp.search(output)
            if vre:
                version = self._expander % vre.groupdict()
        except OSError as e:
            import errno
            if e.errno == errno.ENOENT:
                raise MissingDependencyException(self._dep)
            raise

        return version
