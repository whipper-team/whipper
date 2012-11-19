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
import math
import tempfile
import shutil

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


class Persister(object):
    """
    I wrap an optional pickle to persist an object to disk.

    Instantiate me with a path to automatically unpickle the object.
    Call persist to store the object to disk; it will get stored if it
    changed from the on-disk object.

    @ivar object: the persistent object
    """

    def __init__(self, path=None, default=None):
        """
        If path is not given, the object will not be persisted.
        This allows code to transparently deal with both persisted and
        non-persisted objects, since the persist method will just end up
        doing nothing.
        """
        self._path = path
        self.object = None

        self._unpickle(default)

    def persist(self, obj=None):
        """
        Persist the given object, if we have a persistence path and the
        object changed.

        If object is not given, re-persist our object, always.
        If object is given, only persist if it was changed.
        """
        # don't pickle if it's already ok
        if obj and obj == self.object:
            return

        # store the object on ourselves if not None
        if obj is not None:
            self.object = obj

        # don't pickle if there is no path
        if not self._path:
            return

        # default to pickling our object again
        if obj is None:
            obj = self.object

        # pickle
        self.object = obj
        (fd, path) = tempfile.mkstemp(suffix='.morituri.pickle')
        handle = os.fdopen(fd, 'wb')
        import pickle
        pickle.dump(obj, handle, 2)
        handle.close()
        # do an atomic move
        shutil.move(path, self._path)

    def _unpickle(self, default=None):
        self.object = default

        if not self._path:
            return None

        if not os.path.exists(self._path):
            return None

        handle = open(self._path)
        import pickle

        try:
            self.object = pickle.load(handle)
        except:
            # can fail for various reasons; in that case, pretend we didn't
            # load it
            pass

    def delete(self):
        self.object = None
        os.unlink(self._path)


class PersistedCache(object):
    """
    I wrap a directory of persisted objects.
    """

    path = None

    def __init__(self, path):
        self.path = path
        try:
            os.makedirs(self.path)
        except OSError, e:
            if e.errno != 17: # FIXME
                raise

    def _getPath(self, key):
        return os.path.join(self.path, '%s.pickle' % key)

    def get(self, key):
        """
        Returns the persister for the given key.
        """
        persister = Persister(self._getPath(key))
        if persister.object:
            if hasattr(persister.object, 'instanceVersion'):
                o = persister.object
                if o.instanceVersion < o.__class__.classVersion:
                    persister.delete()

        return persister


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
