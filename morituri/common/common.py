# -*- Mode: Python; test-case-name: morituri.test.test_common_common -*-
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

import os
import os.path
import math
import tempfile
import shutil

from morituri.extern.log import log


SAMPLES_PER_FRAME = 588
WORDS_PER_FRAME = SAMPLES_PER_FRAME * 2
BYTES_PER_FRAME = SAMPLES_PER_FRAME * 4
FRAMES_PER_SECOND = 75


def msfToFrames(msf):
    """
    Converts a string value in MM:SS:FF to frames.

    @param msf: the MM:SS:FF value to convert
    @type  msf: str

    @rtype:   int
    @returns: number of frames
    """
    if not ':' in msf:
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
    """
    Nicely format time in a human-readable format, like
    HH:MM:SS.mmm

    If fractional is zero, no seconds will be shown.
    If it is greater than 0, we will show seconds and fractions of seconds.
    As a side consequence, there is no way to show seconds without fractions.

    @param seconds:    the time in seconds to format.
    @type  seconds:    int or float
    @param fractional: how many digits to show for the fractional part of
                       seconds.
    @type  fractional: int

    @rtype: string
    @returns: a nicely formatted time string.
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


def tagListToDict(tl):
    """
    Removes audio-codec and video-codec since we never set them ourselves.
    """
    import gst

    d = {}
    for key in tl.keys():
        if key == gst.TAG_DATE:
            date = tl[key]
            d[key] = "%4d-%2d-%2d" % (date.year, date.month, date.day)
        elif key in [gst.TAG_AUDIO_CODEC, gst.TAG_VIDEO_CODEC]:
            pass
        else:
            d[key] = tl[key]
    return d


def tagListEquals(tl1, tl2):
    d1 = tagListToDict(tl1)
    d2 = tagListToDict(tl2)

    return d1 == d2


class MissingDependencyException(Exception):
    dependency = None

    def __init__(self, *args):
        self.args = args
        self.dependency = args[0]


class EmptyError(Exception):
    pass


def shrinkPath(path):
    """
    Shrink a full path to a shorter version.
    Used to handle ENAMETOOLONG
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
    """
    Translate a .cue or .toc's FILE to an existing path.

    @type  refPath: unicode
    @type  filePath: unicode
    """
    assert type(filePath) is unicode, "%r is not unicode" % filePath

    if os.path.exists(filePath):
        return filePath

    # .cue FILE statements have Windows-style path separators, so convert
    parts = filePath.split('\\')
    if parts[0] == '':
        parts[0] = os.path.sep
    tpath = os.path.join(*parts)
    candidatePaths = []

    if tpath == os.path.abspath(tpath):
        candidatePaths.append(tpath)
    else:
        # if the path is relative:
        # - check relatively to the cue file
        # - check only the filename part relative to the cue file
        candidatePaths.append(os.path.join(
            os.path.dirname(refPath), tpath))
        candidatePaths.append(os.path.join(
            os.path.dirname(refPath), os.path.basename(tpath)))

    for candidate in candidatePaths:
        noext, _ = os.path.splitext(candidate)
        for ext in ['wav', 'flac']:
            cpath = '%s.%s' % (noext, ext)
            if os.path.exists(cpath):
                return cpath

    raise KeyError("Cannot find file for %r" % filePath)


def getRelativePath(targetPath, collectionPath):
    """
    Get a relative path from the directory of collectionPath to
    targetPath.

    Used to determine the path to use in .cue/.m3u files
    """
    log.debug('common', 'getRelativePath: target %r, collection %r' % (
        targetPath, collectionPath))

    targetDir = os.path.dirname(targetPath)
    collectionDir = os.path.dirname(collectionPath)
    if targetDir == collectionDir:
        log.debug('common',
            'getRelativePath: target and collection in same dir')
        return os.path.basename(targetPath)
    else:
        rel = os.path.relpath(
            targetDir + os.path.sep,
            collectionDir + os.path.sep)
        log.debug('common',
            'getRelativePath: target and collection in different dir, %r' %
                rel)
        return os.path.join(rel, os.path.basename(targetPath))
