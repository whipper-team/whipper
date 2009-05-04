# -*- Mode: Python -*-
# vi:si:et:sw=4:sts=4:ts=4

import os
import tempfile
import shutil

from morituri.common import task, checksum, log
from morituri.program import cdrdao, cdparanoia

import gobject
gobject.threads_init()

def main():
    log.init()
    runner = task.SyncRunner()
    t = cdrdao.ReadIndexTableTask()
    runner.run(t)

    # now check if we have a hidden track one audio
    track = t.toc.tracks[0]
    try:
        index = track.getIndex(0)
    except KeyError:
        print 'No Hidden Track One Audio found.'
        return

    start = index[0]
    stop, _ = track.getIndex(1)
    print 'Found Hidden Track One Audio from frame %d to %d' % (start, stop)
        
    # rip it
    
    checksums = []

    for i in range(2):
        fd, path = tempfile.mkstemp(suffix='.morituri', dir=os.getcwd())
        os.close(fd)

        t = cdparanoia.ReadTrackTask(path, start, stop - 1, offset=0)
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
        shutil.move(path, 'track00.wav')
    else:
        print 'Checksums did not match'
        os.unlink(path)


main()
