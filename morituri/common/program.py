# -*- Mode: Python; test-case-name: morituri.test.test_common_program -*-
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

"""
Common functionality and class for all programs using morituri.
"""

from morituri.common import common
from morituri.result import result
from morituri.program import cdrdao

import os


class Program(object):
    """
    I maintain program state and functionality.
    """

    cuePath = None
    logPath = None

    def __init__(self):
        self.result = result.RipResult()

    def _getTableCachePath(self):
        path = os.path.join(os.path.expanduser('~'), '.morituri', 'cache',
            'table')
        return path

    def unmountDevice(self, device):
        """
        Unmount the given device if it is mounted, as happens with automounted
        data tracks.
        """
        proc = open('/proc/mounts').read()
        if device in proc:
            print 'Device %s is mounted, unmounting' % device
            os.system('umount %s' % device)
        
    def getTable(self, runner, cddbdiscid, device):
        """
        Retrieve the Table either from the cache or the drive.

        @rtype: L{table.Table}
        """
        path = self._getTableCachePath()

        pcache = common.PersistedCache(path)
        ptable = pcache.get(cddbdiscid)

        if not ptable.object:
            t = cdrdao.ReadTableTask(device=device)
            runner.run(t)
            ptable.persist(t.table)
        itable = ptable.object
        assert itable.hasTOC()

        self.result.table = itable

        return itable

    def writeCue(self, discName):
        assert self.result.table.canCue()

        cuePath = '%s.cue' % discName
        handle = open(cuePath, 'w')
        # FIXME: do we always want utf-8 ?
        handle.write(self.result.table.cue().encode('utf-8'))
        handle.close()

        self.cuePath = cuePath

        return cuePath

    def writeLog(self, discName, logger):
        logPath = '%s.log' % discName
        handle = open(logPath, 'w')
        handle.write(logger.log(res).encode('utf-8'))
        handle.close()

        self.logPath = logPath

        return logPath
