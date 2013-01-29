# -*- Mode: Python; test-case-name: morituri.test.test_common_cache -*-
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
import glob
import tempfile
import shutil

from morituri.result import result
from morituri.extern.log import log


class Persister(log.Loggable):
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
        self.debug('saved persisted object to %r' % self._path)

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
            self.debug('loaded persisted object from %r' % self._path)
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
        # FIXME: don't delete old objects atm
        # if persister.object:
        #     if hasattr(persister.object, 'instanceVersion'):
        #         o = persister.object
        #         if o.instanceVersion < o.__class__.classVersion:
        #             persister.delete()

        return persister


class ResultCache(log.Loggable):

    def __init__(self, path=None):
        if not path:
            path = self._getResultCachePath()

        self._path = path
        self._pcache = PersistedCache(self._path)

    def _getResultCachePath(self):
        path = os.path.join(os.path.expanduser('~'), '.morituri', 'cache',
            'result')
        return path

    def getRipResult(self, cddbdiscid, create=True):
        """
        Retrieve the persistable RipResult either from our cache (from a
        previous, possibly aborted rip), or return a new one.

        @rtype: L{Persistable} for L{result.RipResult}
        """
        presult = self._pcache.get(cddbdiscid)

        if not presult.object:
            self.debug('result for cddbdiscid %r not in cache', cddbdiscid)
            if not create:
                self.debug('returning None')
                return None

            self.debug('creating result')
            presult.object = result.RipResult()
            presult.persist(presult.object)
        else:
            self.debug('result for cddbdiscid %r found in cache, reusing',
                cddbdiscid)

        return presult

    def getIds(self):
        paths = glob.glob(os.path.join(self._path, '*.pickle'))

        return [os.path.splitext(os.path.basename(path))[0] for path in paths]
        
