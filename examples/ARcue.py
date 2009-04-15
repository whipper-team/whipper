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
import optparse

import gobject
gobject.threads_init()
import gtk

from morituri.image import image
from morituri.common import task, crc

def gtkmain(runner, taskk):
    runner.connect('stop', lambda _: gtk.main_quit())

    window = gtk.Window()
    window.add(progress)
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

    options, args = parser.parse_args(argv[1:])

    path = 'test.cue'

    try:
        path = sys.argv[1]
    except IndexError:
        pass

    cueImage = image.Image(path)
    verifytask = image.ImageVerifyTask(cueImage)
    cuetask = image.AudioRipCRCTask(cueImage)

    if options.runner == 'cli':
        runner = task.SyncRunner()
        function = climain
    elif options.runner == 'gtk':
        runner = task.GtkProgressRunner()
        function = gtkmain

    cueImage.setup(runner)
    print "CDDB disc id", cueImage.toc.getCDDBDiscId()
    url = cueImage.toc.getAccurateRipURL()
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

        if responses[0].cddbDiscId != cueImage.toc.getCDDBDiscId():
            print "AccurateRip response discid different: %s" % \
                responses[0].cddbDiscId

    function(runner, verifytask)
    function(runner, cuetask)

    response = None

    for i, crc in enumerate(cuetask.crcs):
        status = 'rip NOT accurate'

        confidence = None
        arcrc = None

        for j, r in enumerate(responses):
            if "%08x" % crc == r.crcs[i]:
                if not response:
                    response = r
                else:
                    assert r == response, \
                        "CRC %s for %d matches wrong response %d, crc %s" % (
                            crc, i + 1, j + 1, response.crcs[i])
                status = 'rip accurate    '
                arcrc = crc
                confidence = response.confidences[i]

        c = "(not found)"
        ar = ""
        if responses:
            maxConfidence = max(r.confidences[i] for r in responses)
                 
            c = "(confidence %3d)" % maxConfidence
            if confidence is not None:
                if confidence < maxConfidence:
                    c = "(confidence %3d of %3d)" % (confidence, maxConfidence)

            ar = " AR [%s]" % response.crcs[i]
        print "Track %2d: %s %s mine [%08x] %s" % (
            i + 1, status, c, crc, ar)


main(sys.argv)
