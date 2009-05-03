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
import gtk

from morituri.image import image
from morituri.common import task, taskgtk, checksum
from morituri.program import cdrdao, cdparanoia

"""
Find read offset by ripping a track from an AccurateRip CD.
"""

from morituri.common import log
log.init()

def gtkmain(runner, taskk):
    runner.connect('stop', lambda _: gtk.main_quit())

    window = gtk.Window()
    window.add(runner)
    window.show_all()

    runner.run(taskk)

    gtk.main()

def climain(runner, taskk):
    runner.run(taskk)


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
    t = cdrdao.ReadTableTask()

    if options.runner == 'cli':
        runner = task.SyncRunner()
        function = climain
    elif options.runner == 'gtk':
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
        else:
            raise

    if responses:
        print '%d AccurateRip reponses found' % len(responses)

        if responses[0].cddbDiscId != table.getCDDBDiscId():
            print "AccurateRip response discid different: %s" % \
                responses[0].cddbDiscId

    response = None

    # now rip the first track at various offsets, calculating AccurateRip
    # CRC, and matching it against the retrieved ones
    for offset in offsets:
        fd, path = tempfile.mkstemp(suffix='.morituri')
        os.close(fd)

        print 'ripping track 1 with offset', offset
        track = table.tracks[0]
        t = cdparanoia.ReadTrackTask(path, track.start, track.end, offset)
        t.description = 'Ripping with offset %d' % offset
        function(runner, t)

        t = checksum.AccurateRipChecksumTask(path, trackNumber=1,
            trackCount = len(table.tracks))
        function(runner, t)
        arcs = "%08x" % t.checksum
        print 'AR checksum calculated: %s' % arcs

        for i, r in enumerate(responses):
            if arcs == r.checksums[0]:
                print 'MATCHED against response %d' % i
                print 'offset of device is', offset


main(sys.argv)
