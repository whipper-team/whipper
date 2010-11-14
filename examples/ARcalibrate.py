# -*- Mode: Python; test-case-name: morituri.test.test_header -*-
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
import sys
import tempfile
import optparse

import gobject
gobject.threads_init()

from morituri.image import image
from morituri.common import task, checksum
from morituri.program import cdrdao, cdparanoia

"""
Find read offset by ripping a track from an AccurateRip CD.
"""

from morituri.common import log
log.init()

def gtkmain(runner, taskk):
    import gtk
    runner.connect('stop', lambda _: gtk.main_quit())

    window = gtk.Window()
    window.add(runner)
    window.show_all()

    runner.run(taskk)

    gtk.main()

def climain(runner, taskk):
    runner.run(taskk)


def arcs(runner, function, table, track, offset):
    # rips the track with the given offset, return the arcs checksum
    print 'ripping track %r with offset %d' % (track, offset)

    fd, path = tempfile.mkstemp(suffix='.track%02d.offset%d.morituri.wav' % (
        track, offset))
    os.close(fd)

    table.getTrackLength
    t = cdparanoia.ReadTrackTask(path, table, table.getTrackStart(track),
        table.getTrackEnd(track), offset)
    t.description = 'Ripping with offset %d' % offset
    function(runner, t)

    t = checksum.AccurateRipChecksumTask(path, trackNumber=track,
        trackCount=len(table.tracks))
    function(runner, t)
    
    os.unlink(path)
    return "%08x" % t.checksum
 
def main(argv):
    parser = optparse.OptionParser()

    default = 'cli'
    parser.add_option('-r', '--runner',
        action="store", dest="runner",
        help="runner ('cli' or 'gtk', defaults to %s)" % default,
        default=default)

    # see http://www.accuraterip.com/driveoffsets.htm
    default = "0, 6, 12, 48, 91, 97, 102, 108, 120, " + \
        "564, 594, 667, 685, 691, 704, 738, 1194, 1292, 1336, 1776, -582"
    parser.add_option('-o', '--offsets',
        action="store", dest="offsets",
        help="list of offsets, comma-separated, "
            "colon-separated for ranges (defaults to %s)" %
            default,
        default=default)

    options, args = parser.parse_args(argv[1:])

    offsets = []
    blocks = options.offsets.split(',')
    for b in blocks:
        if ':' in b:
            a, b = b.split(':')
            offsets.extend(range(int(a), int(b) + 1))
        else:
            offsets.append(int(b))

    # first get the Table Of Contents of the CD
    t = cdrdao.ReadTOCTask()

    if options.runner == 'cli':
        runner = task.SyncRunner()
        function = climain
    elif options.runner == 'gtk':
        from morituri.common import taskgtk
        runner = taskgtk.GtkProgressRunner()
        function = gtkmain

    function(runner, t)
    table = t.table

    print "CDDB disc id", table.getCDDBDiscId()
    url = table.getAccurateRipURL()
    print "AccurateRip URL", url

    # FIXME: download url as a task too
    responses = []
    import urllib2
    try:
        handle = urllib2.urlopen(url)
        data = handle.read()
        responses = image.getAccurateRipResponses(data)
    except urllib2.HTTPError, e:
        if e.code == 404:
            print 'Album not found in AccurateRip database'
            sys.exit(1)
        else:
            raise

    if responses:
        print '%d AccurateRip responses found' % len(responses)

        if responses[0].cddbDiscId != table.getCDDBDiscId():
            print "AccurateRip response discid different: %s" % \
                responses[0].cddbDiscId

    # now rip the first track at various offsets, calculating AccurateRip
    # CRC, and matching it against the retrieved ones
    
    def match(archecksum, track, responses):
        for i, r in enumerate(responses):
            if archecksum == r.checksums[track - 1]:
                return archecksum, i

        return None, None

    for offset in offsets:
        archecksum = arcs(runner, function, table, 1, offset)

        print 'AR checksum calculated: %s' % archecksum

        c, i = match(archecksum, 1, responses)
        if c:
            count = 1
            print 'MATCHED against response %d' % i
            print 'offset of device is likely', offset
            # now try and rip all other tracks as well
            for track in range(2, len(table.tracks) + 1):
                archecksum = arcs(runner, function, table, track, offset)
                c, i = match(archecksum, track, responses)
                if c:
                    print 'MATCHED track %d against response %d' % (track, i)
                    count += 1

            if count == len(table.tracks):
                print 'OFFSET of device is', offset
                return
            else:
                print 'not all tracks matched, continuing'
                
    print 'no matching offset found.'
                    
                


main(sys.argv)
