# -*- Mode: Python -*-
# vi:si:et:sw=4:sts=4:ts=4

import re
import os
import stat
import subprocess
import tempfile

from morituri.common import task, checksum, log
from morituri.image import table
from morituri.program import cdparanoia

import gobject
gobject.threads_init()

def main():
    log.init()
    runner = task.SyncRunner()

    checksums = []
    for i in range(2):
        fd, path = tempfile.mkstemp(suffix='.morituri')
        os.close(fd)

        fakeTable = table.Table([
            table.Track( 1,      0,  15536),
        ])

        t = cdparanoia.ReadTrackTask(path, fakeTable, 1000, 3000, offset=0)

        if i == 1:
            t.description = 'Verifying track...'

        runner.run(t)

        t = checksum.CRC32Task(path)
        runner.run(t)

        if i == 0:
            os.unlink(path)

        checksums.append(t.checksum)

    print 'runner done'
    if checksums[0] == checksums[1]:
        print 'Checksums match'
    else:
        print 'Checksums do not match'


main()
