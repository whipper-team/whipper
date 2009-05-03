# -*- Mode: Python -*-
# vi:si:et:sw=4:sts=4:ts=4

import re
import os
import sys
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
    if len(sys.argv) > 1:
        path = sys.argv[1]
    else:
        fd, path = tempfile.mkstemp(suffix='.morituri.wav')
        os.close(fd)
        print 'storing track to %s' % path

    fakeTable = table.Table([
        table.Track( 1,      0,  15536),
    ])

    t = cdparanoia.ReadVerifyTrackTask(path, fakeTable, 1000, 3000, offset=0)


    runner.run(t)

    print 'runner done'

    if t.checksum is not None:
        print 'Checksums match'
    else:
        print 'Checksums do not match'


main()
