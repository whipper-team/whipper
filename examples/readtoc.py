# -*- Mode: Python -*-
# vi:si:et:sw=4:sts=4:ts=4

from morituri.common import task, log
from morituri.program import cdrdao

def main():
    log.init()
    runner = task.SyncRunner()
    t = cdrdao.ReadTableTask()
    runner.run(t)
    print 'runner done', t.toc

    if not t.table:
        print 'Failed to read TOC'
        return

    for track in t.table.tracks:
        print track.getIndex(1).absolute

main()
