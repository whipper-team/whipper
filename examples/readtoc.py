# -*- Mode: Python -*-
# vi:si:et:sw=4:sts=4:ts=4

from morituri.common import task, log
from morituri.program import cdrdao

def main():
    log.init()
    runner = task.SyncRunner()
    t = cdrdao.ReadTOCTask()
    runner.run(t)
    print 'runner done', t.toc

    for track in t.toc.tracks:
        print track._indexes
        

main()
