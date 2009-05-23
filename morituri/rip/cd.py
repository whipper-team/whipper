# -*- Mode: Python -*-
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
import tempfile
import sys
import pickle
import shutil

import gobject
gobject.threads_init()

from morituri.common import logcommand, task, checksum, common, accurip
from morituri.image import image, cue, table
from morituri.program import cdrdao, cdparanoia

class TrackMetadata(object):
    artist = None
    title = None

class DiscMetadata(object):
    artist = None
    title = None
    various = False
    tracks = None

    def __init__(self):
        self.tracks = []

def filterForPath(text):
    return "-".join(text.split("/"))

def musicbrainz(discid):
    metadata = DiscMetadata()

    import musicbrainz2.disc as mbdisc
    import musicbrainz2.webservice as mbws


    # Setup a Query object.
    service = mbws.WebService()
    query = mbws.Query(service)


    # Query for all discs matching the given DiscID.
    try:
        filter = mbws.ReleaseFilter(discId=discid)
        results = query.getReleases(filter)
    except mbws.WebServiceError, e:
        print "Error:", e
        return


    # No disc matching this DiscID has been found.
    if len(results) == 0:
        print "Disc is not yet in the MusicBrainz database."
        print "Consider adding it."
        return


    # Display the returned results to the user.
    print 'Matching releases:'

    for result in results:
        release = result.release
        print 'Artist  :', release.artist.name
        print 'Title   :', release.title
        print


    # Select one of the returned releases. We just pick the first one.
    selectedRelease = results[0].release


    # The returned release object only contains title and artist, but no tracks.
    # Query the web service once again to get all data we need.
    try:
        inc = mbws.ReleaseIncludes(artist=True, tracks=True, releaseEvents=True)
        release = query.getReleaseById(selectedRelease.getId(), inc)
    except mbws.WebServiceError, e:
        print "Error:", e
        sys.exit(2)


    isSingleArtist = release.isSingleArtistRelease()
    metadata.various = not isSingleArtist
    metadata.title = release.title
    metadata.artist = release.artist.getUniqueName()

    print "%s - %s" % (release.artist.getUniqueName(), release.title)

    i = 1
    for t in release.tracks:
        track = TrackMetadata()
        if isSingleArtist:
            track.artist = metadata.artist
            track.title = t.title
        else:
            track.artist = t.artist.name
            track.title = t.title
        metadata.tracks.append(track)

    return metadata

def getPath(template, metadata, i):
    # returns without extension

    v = {}

    v['t'] = '%02d' % (i + 1)

    # default values
    v['A'] = 'Unknown Artist'
    v['d'] = 'Unknown Disc'

    v['a'] = v['A']
    v['n'] = 'Unknown Track'

    if metadata:
        v['A'] = filterForPath(metadata.artist)
        v['d'] = filterForPath(metadata.title)
        if i >= 0:
            v['a'] = filterForPath(metadata.tracks[i].artist)
            v['n'] = filterForPath(metadata.tracks[i].title)
        else:
            # htoa defaults to disc's artist
            v['a'] = filterForPath(metadata.artist)
            v['n'] = filterForPath('Hidden Track One Audio')

    import re
    template = re.sub(r'%(\w)', r'%(\1)s', template)

    return template % v

class Rip(logcommand.LogCommand):
    summary = "rip CD"

    def addOptions(self):
        # FIXME: get from config
        default = 0
        self.parser.add_option('-o', '--offset',
            action="store", dest="offset",
            help="sample offset (defaults to %d)" % default,
            default=default)
        # FIXME: have a cache of these pickles somewhere
        self.parser.add_option('-t', '--table-pickle',
            action="store", dest="table_pickle",
            help="pickle to use for reading and writing the table",
            default=default)
        self.parser.add_option('-T', '--toc-pickle',
            action="store", dest="toc_pickle",
            help="pickle to use for reading and writing the TOC",
            default=default)
        # FIXME: get from config
        default = '%A - %d/%t. %a - %n'
        self.parser.add_option('', '--track-template',
            action="store", dest="track_template",
            help="template for track file naming (default %s)" % default,
            default=default)
        default = '%A - %d/%A - %d'
        self.parser.add_option('', '--disc-template',
            action="store", dest="disc_template",
            help="template for disc file naming (default %s)" % default,
            default=default)


    def do(self, args):
        runner = task.SyncRunner()
        def function(r, t):
            r.run(t)

        # first, read the normal TOC, which is fast
        ptoc = common.Persister(self.options.toc_pickle or None)
        if not ptoc.object:
            t = cdrdao.ReadTOCTask()
            function(runner, t)
            ptoc.persist(t.table)
        ittoc = ptoc.object
        assert ittoc.hasTOC()

        # already show us some info based on this
        print "CDDB disc id", ittoc.getCDDBDiscId()
        metadata = musicbrainz(ittoc.getMusicBrainzDiscId())

        url = ittoc.getAccurateRipURL()
        print "AccurateRip URL", url

        cache = accurip.AccuCache()
        responses = cache.retrieve(url)

        # now, read the complete index table, which is slower
        ptable = common.Persister(self.options.table_pickle or None)
        if not ptable.object:
            t = cdrdao.ReadTableTask()
            function(runner, t)
            ptable.persist(t.table)
        itable = ptable.object

        assert itable.hasTOC()

        assert itable.getCDDBDiscId() == ittoc.getCDDBDiscId(), \
            "full table's id %s differs from toc id %s" % (
                itable.getCDDBDiscId(), ittoc.getCDDBDiscId())
        assert itable.getMusicBrainzDiscId() == ittoc.getMusicBrainzDiscId()

        lastTrackStart = 0

        # check for hidden track one audio
        htoapath = None
        index = None
        track = itable.tracks[0]
        try:
            index = track.getIndex(0)
        except KeyError:
            pass

        if index:
            start = index.absolute
            stop = track.getIndex(1).absolute
            print 'Found Hidden Track One Audio from frame %d to %d' % (start, stop)
                
            # rip it
            htoapath = getPath(self.options.track_template, metadata, -1) + '.wav'
            htoalength = stop - start
            if not os.path.exists(htoapath):
                print 'Ripping track %d: %s' % (0, os.path.basename(htoapath))
                t = cdparanoia.ReadVerifyTrackTask(htoapath, ittoc,
                    start, stop - 1,
                    offset=int(self.options.offset))
                function(runner, t)
                if t.checksum:
                    print 'Checksums match for track %d' % 0
                else:
                    print 'ERROR: checksums did not match for track %d' % 0
                # overlay this rip onto the Table
            itable.setFile(1, 0, htoapath, htoalength, 0)


        for i, track in enumerate(itable.tracks):
            path = getPath(self.options.track_template, metadata, i) + '.wav'
            dirname = os.path.dirname(path)
            if not os.path.exists(dirname):
                os.makedirs(dirname)

            # FIXME: optionally allow overriding reripping
            if not os.path.exists(path):
                print 'Ripping track %d: %s' % (i + 1, os.path.basename(path))
                t = cdparanoia.ReadVerifyTrackTask(path, ittoc,
                    ittoc.getTrackStart(i + 1),
                    ittoc.getTrackEnd(i + 1),
                    offset=int(self.options.offset))
                t.description = 'Reading Track %d' % (i + 1)
                function(runner, t)
                if t.checksum:
                    print 'Checksums match for track %d' % (i + 1)
                else:
                    print 'ERROR: checksums did not match for track %d' % (i + 1)

            # overlay this rip onto the Table
            itable.setFile(i + 1, 1, path, ittoc.getTrackLength(i + 1), i + 1)


        ### write disc files
        discName = getPath(self.options.disc_template, metadata, i)
        dirname = os.path.dirname(discName)
        if not os.path.exists(dirname):
            os.makedirs(dirname)

        # write .cue file
        cuePath = '%s.cue' % discName
        handle = open(cuePath, 'w')
        handle.write(itable.cue())
        handle.close()

        # write .m3u file
        m3uPath = '%s.m3u' % discName
        handle = open(m3uPath, 'w')
        handle.write('#EXTM3U\n')
        if htoapath:
            handle.write('#EXTINF:%d,%s\n' % (
                htoalength / common.FRAMES_PER_SECOND,
                    os.path.basename(htoapath[:-4])))
            handle.write('%s\n' % os.path.basename(htoapath))

        for i, track in enumerate(itable.tracks):
            path = getPath(self.options.track_template, metadata, i) + '.wav'
            handle.write('#EXTINF:%d,%s\n' % (
                itable.getTrackLength(i + 1) / common.FRAMES_PER_SECOND,
                os.path.basename(path)))
            handle.write('%s\n' % os.path.basename(path))
        handle.close()

        # verify using accuraterip
        print "CDDB disc id", itable.getCDDBDiscId()
        print "MusicBrainz disc id", itable.getMusicBrainzDiscId()
        url = itable.getAccurateRipURL()
        print "AccurateRip URL", url

        cache = accurip.AccuCache()
        responses = cache.retrieve(url)
        if not responses:
            print 'Album not found in AccurateRip database'

        if responses:
            print '%d AccurateRip reponses found' % len(responses)

            if responses[0].cddbDiscId != itable.getCDDBDiscId():
                print "AccurateRip response discid different: %s" % \
                    responses[0].cddbDiscId

           
        # FIXME: put accuraterip verification into a separate task/function
        # and apply here
        cueImage = image.Image(cuePath)
        verifytask = image.ImageVerifyTask(cueImage)
        cuetask = image.AccurateRipChecksumTask(cueImage)
        function(runner, verifytask)
        function(runner, cuetask)

        response = None # track which response matches, for all tracks

        # loop over tracks
        for i, sum in enumerate(cuetask.checksums):
            status = 'rip NOT accurate'

            confidence = None
            arsum = None

            # match against each response's checksum
            for j, r in enumerate(responses):
                if "%08x" % sum == r.checksums[i]:
                    if not response:
                        response = r
                    else:
                        assert r == response, \
                            "checksum %s for %d matches wrong response %d, "\
                            "checksum %s" % (
                                sum, i + 1, j + 1, response.checksums[i])
                    status = 'rip accurate    '
                    arsum = sum
                    confidence = response.confidences[i]

            c = "(not found)"
            ar = "(not in database)"
            if responses:
                if not response:
                    print 'ERROR: none of the responses matched.'
                else:
                    maxConfidence = max(r.confidences[i] for r in responses)
                         
                    c = "(max confidence %3d)" % maxConfidence
                    if confidence is not None:
                        if confidence < maxConfidence:
                            c = "(confidence %3d of %3d)" % (confidence, maxConfidence)

                    ar = ", AR [%s]" % response.checksums[i]
            print "Track %2d: %s %s [%08x]%s" % (
                i + 1, status, c, sum, ar)

class CD(logcommand.LogCommand):
    summary = "handle CD's"

    subCommandClasses = [Rip, ]
