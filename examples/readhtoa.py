# -*- Mode: Python -*-
# vi:si:et:sw=4:sts=4:ts=4

import os
import sys
import optparse
import tempfile
import shutil

from morituri.common import task, checksum, log
from morituri.program import cdrdao, cdparanoia

import gobject
gobject.threads_init()

def main():
    log.init()

    parser = optparse.OptionParser()

    default = 0
    parser.add_option('-o', '--offset',
        action="store", dest="offset",
        help="sample offset (defaults to %d)" % default,
        default=default)

    options, args = parser.parse_args(sys.argv[1:])

    runner = task.SyncRunner()

    # first do a simple TOC scan
    t = cdrdao.ReadTOCTask()
    runner.run(t)
    toc = t.table

    offset = t.table.tracks[0].getIndex(1).absolute

    if offset < 150:
        print 'Disc is unlikely to have Hidden Track One Audio.'
    else:
        print 'Disc seems to have a %d frame HTOA.' % offset


    # now do a more extensive scan
    t = cdrdao.ReadTableTask()
    runner.run(t)

    # now check if we have a hidden track one audio
    track = t.table.tracks[0]
    try:
        index = track.getIndex(0)
    except KeyError:
        print 'No Hidden Track One Audio found.'
        return

    start = index.absolute
    stop = track.getIndex(1).absolute
    print 'Found Hidden Track One Audio from frame %d to %d' % (start, stop)
        
    # rip it
    riptask = cdparanoia.ReadVerifyTrackTask('track00.wav', t.table,
        start, stop - 1,
        offset=int(options.offset))
    runner.run(riptask)

    print 'runner done'

    if riptask.checksum is not None:
        print 'Checksums match'
    else:
        print 'Checksums did not match'

main()
