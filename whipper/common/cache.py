# -*- Mode: Python; test-case-name: whipper.test.test_common_cache -*-
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
import glob
import tempfile
import shutil

from whipper.result import result
from whipper.common import directory

import logging
logger = logging.getLogger(__name__)


class Persister:
    """I wrap an optional pickle to persist an object to disk.

    Instantiate me with a path to automatically unpickle the object.
    Call persist to store the object to disk; it will get stored if it
    changed from the on-disk object.

    If path is not given, the object will not be persisted.
    This allows code to transparently deal with both persisted and
    non-persisted objects, since the persist method will just end up
    doing nothing.

    :ivar object: the persistent object.
    :vartype object:
    :ivar path:
    :vartype path:
    """

    def __init__(self, path=None, default=None):
        self._path = path
        self.object = None

        self._unpickle(default)

    def persist(self, obj=None):
        """Persist the given object.

        If we have a persistence path and the object changed.

        If object is not given, re-persist our object, always.
        If object is given, only persist if it was changed.

        :param obj:  (Default value = None).
        :type obj:
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
        (fd, path) = tempfile.mkstemp(suffix='.whipper.pickle')
        handle = os.fdopen(fd, 'wb')
        import pickle
        pickle.dump(obj, handle, 2)
        handle.close()
        # do an atomic move
        shutil.move(path, self._path)
        logger.debug('saved persisted object to %r' % self._path)

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
            logger.debug('loaded persisted object from %r' % self._path)
        except Exception as e:
            # TODO: restrict kind of caught exceptions?
            # can fail for various reasons; in that case, pretend we didn't
            # load it
            logger.debug(e)
            pass

    def delete(self):
        self.object = None
        os.unlink(self._path)


class PersistedCache:
    """I wrap a directory of persisted objects."""

    path = None

    def __init__(self, path):
        self.path = path
        try:
            os.makedirs(self.path)
        except OSError as e:
            if e.errno != 17:  # FIXME
                raise

    def _getPath(self, key):
        return os.path.join(self.path, '%s.pickle' % key)

    def get(self, key):
        """Return the persister for the given key.

        :param key:
        :type key:
        """
        persister = Persister(self._getPath(key))
        if persister.object:
            if hasattr(persister.object, 'instanceVersion'):
                o = persister.object
                if o.instanceVersion < o.__class__.classVersion:
                    logger.debug(
                        'key %r persisted object version %d is outdated',
                        key, o.instanceVersion)
                    persister.object = None
        # FIXME: don't delete old objects atm
        #             persister.delete()

        return persister


class ResultCache:

    def __init__(self, path=None):
        self._path = path or directory.cache_path('result')
        self._pcache = PersistedCache(self._path)

    def getRipResult(self, cddbdiscid, create=True):
        """Retrieve the persistable RipResult.

        The RipResult is retrieved either from our cache (from a previous,
        possibly aborted rip), or a new one is returned.

        :param cddbdiscid:
        :type cddbdiscid:
        :param create:  (Default value = True).
        :type create:
        :rtype: L{Persistable} for L{result.RipResult}
        """
        presult = self._pcache.get(cddbdiscid)

        if not presult.object:
            logger.debug('result for cddbdiscid %r not in cache', cddbdiscid)
            if not create:
                logger.debug('returning None')
                return None

            logger.debug('creating result')
            presult.object = result.RipResult()
            presult.persist(presult.object)
        else:
            logger.debug('result for cddbdiscid %r found in cache, reusing',
                         cddbdiscid)

        return presult

    def getIds(self):
        paths = glob.glob(os.path.join(self._path, '*.pickle'))

        return [os.path.splitext(os.path.basename(path))[0] for path in paths]


class TableCache:
    """I read and write entries to and from the cache of tables.

    If no path is specified, the cache will write to the current cache
    directory and read from all possible cache directories (to allow for
    pre-0.2.1 cddbdiscid-keyed entries).
    """

    def __init__(self, path=None):
        if not path:
            self._path = directory.cache_path('table')
        else:
            self._path = path

        self._pcache = PersistedCache(self._path)

    def get(self, cddbdiscid, mbdiscid):
        # Before 0.2.1, we only saved by cddbdiscid, and had collisions
        # mbdiscid collisions are a lot less likely
        ptable = self._pcache.get('mbdiscid.' + mbdiscid)

        if not ptable.object:
            ptable = self._pcache.get(cddbdiscid)
            if ptable.object:
                if ptable.object.getMusicBrainzDiscId() != mbdiscid:
                    logger.debug('cached table is for different mb id %r' % (
                        ptable.object.getMusicBrainzDiscId()))
                ptable.object = None
            else:
                logger.debug('no valid cached table found for %r' %
                             cddbdiscid)

        if not ptable.object:
            # get an empty persistable from the writable location
            ptable = self._pcache.get('mbdiscid.' + mbdiscid)

        return ptable
