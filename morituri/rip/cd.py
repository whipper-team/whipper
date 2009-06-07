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
import sys
import math

import cdio

import gobject
gobject.threads_init()

import gst

from morituri.common import logcommand, task, checksum, common, accurip, log
from morituri.common import drive, encode
from morituri.result import result
from morituri.image import image, cue, table
from morituri.program import cdrdao, cdparanoia

class TrackMetadata(object):
    artist = None
    title = None

class DiscMetadata(object):
    """
    @param release: earliest release date, in YYYY-MM-DD
    @type  release: unicode
    """
    artist = None
    title = None
    various = False
    tracks = None
    release = None

    def __init__(self):
        self.tracks = []

def filterForPath(text):
    return "-".join(text.split("/"))

def musicbrainz(discid):
    metadata = DiscMetadata()

    #import musicbrainz2.disc as mbdisc
    import musicbrainz2.webservice as mbws


    # Setup a Query object.
    service = mbws.WebService()
    query = mbws.Query(service)


    # Query for all discs matching the given DiscID.
    try:
        rfilter = mbws.ReleaseFilter(discId=discid)
        results = query.getReleases(rfilter)
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


    # convert to our objects
    isSingleArtist = release.isSingleArtistRelease()
    metadata.various = not isSingleArtist
    metadata.title = release.title
    # getUniqueName gets disambiguating names like Muse (UK rock band)
    metadata.artist = release.artist.name
    metadata.release = release.getEarliestReleaseDate()

    print "%s - %s" % (release.artist.name, release.title)

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

def getPath(outdir, template, metadata, mbdiscid, i):
    """
    Based on the template, get a complete path for the given track,
    minus extension.
    Also works for the disc name, using disc variables for the template.

    @param outdir:   the directory where to write the files
    @type  outdir:   str
    @param template: the template for writing the file
    @type  template: str
    @param metadata:
    @type  metadata: L{DiscMetadata}
    @param i:        track number (0 for HTOA)
    @type  i:        int
    """
    # returns without extension

    v = {}

    v['t'] = '%02d' % i

    # default values
    v['A'] = 'Unknown Artist'
    v['d'] = mbdiscid

    v['a'] = v['A']
    v['n'] = 'Unknown Track %d' % i

    if metadata:
        v['A'] = filterForPath(metadata.artist)
        v['d'] = filterForPath(metadata.title)
        if i > 0:
            try:
                v['a'] = filterForPath(metadata.tracks[i - 1].artist)
                v['n'] = filterForPath(metadata.tracks[i - 1].title)
            except IndexError, e:
                print 'ERROR: no track %d found, %r' % (i, e)
                raise
        else:
            # htoa defaults to disc's artist
            v['a'] = filterForPath(metadata.artist)
            v['n'] = filterForPath('Hidden Track One Audio')

    import re
    template = re.sub(r'%(\w)', r'%(\1)s', template)

    return os.path.join(outdir, template % v)

def getTagList(metadata, i):
    """
    Based on the metadata, get a gst.TagList for the given track.

    @param metadata:
    @type  metadata: L{DiscMetadata}
    @param i:        track number (0 for HTOA)
    @type  i:        int

    @rtype: L{gst.TagList}
    """
    artist = u'Unknown Artist'
    disc = u'Unknown Disc'
    title = u'Unknown Track'

    if metadata:
        artist = metadata.artist
        disc = metadata.title
        if i > 0:
            try:
                artist = metadata.tracks[i - 1].artist
                title = metadata.tracks[i - 1].title
            except IndexError, e:
                print 'ERROR: no track %d found, %r' % (i, e)
                raise
        else:
            # htoa defaults to disc's artist
            title = 'Hidden Track One Audio'

    ret = gst.TagList()

    # gst-python 0.10.15.1 does not handle unicode -> utf8 string conversion
    # see http://bugzilla.gnome.org/show_bug.cgi?id=584445
    ret[gst.TAG_ARTIST] = artist.encode('utf-8')
    ret[gst.TAG_TITLE] = title.encode('utf-8')
    ret[gst.TAG_ALBUM] = disc.encode('utf-8')

    # gst-python 0.10.15.1 does not handle tags that are UINT
    # see gst-python commit 26fa6dd184a8d6d103eaddf5f12bd7e5144413fb
    # FIXME: no way to compare against 'master' version after 0.10.15
    if gst.pygst_version >= (0, 10, 15):
        ret[gst.TAG_TRACK_NUMBER] = i
    if metadata:
        # works, but not sure we want this
        # if gst.pygst_version >= (0, 10, 15):
        #     ret[gst.TAG_TRACK_COUNT] = len(metadata.tracks)
        # hack to get a GstDate which we cannot instantiate directly in
        # 0.10.15.1
        # FIXME: The dates are strings and must have the format 'YYYY',
        # 'YYYY-MM' or 'YYYY-MM-DD'.
        # GstDate expects a full date, so default to Jan and 1st if MM and DD
        # are missing
        date = metadata.release
        if date:
            log.debug('metadata',
                'Converting release date %r to structure', date)
            if len(date) == 4:
                date += '-01'
            if len(date) == 7:
                date += '-01'

            s = gst.structure_from_string('hi,date=(GstDate)%s' %
                str(date))
            ret[gst.TAG_DATE] = s['date']
        
    # FIXME: gst.TAG_ISRC 

    return ret

class Rip(logcommand.LogCommand):
    summary = "rip CD"

    def addOptions(self):
        # FIXME: get from config
        default = 0
        self.parser.add_option('-o', '--offset',
            action="store", dest="offset",
            help="sample read offset (defaults to %d)" % default,
            default=default)
        self.parser.add_option('-O', '--output-directory',
            action="store", dest="output_directory",
            help="output directory (defaults to current directory)")
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
        default = 'flac'
        self.parser.add_option('', '--profile',
            action="store", dest="profile",
            help="profile for encoding (default '%s', choices '%s')" % (
                default, "', '".join(encode.PROFILES.keys())),
            default=default)


    def do(self, args):
        runner = task.SyncRunner()
        def function(r, t):
            r.run(t)

        # if the device is mounted (data session), unmount it
        device = self.parentCommand.options.device
        print 'Checking device', device

        proc = open('/proc/mounts').read()
        if device in proc:
            print 'Device %s is mounted, unmounting' % device
            os.system('umount %s' % device)
        
        # first, read the normal TOC, which is fast
        ptoc = common.Persister(self.options.toc_pickle or None)
        if not ptoc.object:
            t = cdrdao.ReadTOCTask(device=device)
            function(runner, t)
            ptoc.persist(t.table)
        ittoc = ptoc.object
        assert ittoc.hasTOC()

        # already show us some info based on this
        print "CDDB disc id", ittoc.getCDDBDiscId()
        mbdiscid = ittoc.getMusicBrainzDiscId()
        print "MusicBrainz disc id", mbdiscid

        metadata = musicbrainz(mbdiscid)
        if not metadata:
            print 'Submit this disc to MusicBrainz at:'
            print ittoc.getMusicBrainzSubmitURL()

        # now, read the complete index table, which is slower
        path = os.path.join(os.path.expanduser('~'), '.morituri', 'cache',
            'table')
        pcache = common.PersistedCache(path)
        ptable = pcache.get(ittoc.getCDDBDiscId())
        if not ptable.object:
            t = cdrdao.ReadTableTask(device=self.parentCommand.options.device)
            function(runner, t)
            ptable.persist(t.table)
        itable = ptable.object

        assert itable.hasTOC()

        assert itable.getCDDBDiscId() == ittoc.getCDDBDiscId(), \
            "full table's id %s differs from toc id %s" % (
                itable.getCDDBDiscId(), ittoc.getCDDBDiscId())
        assert itable.getMusicBrainzDiscId() == ittoc.getMusicBrainzDiscId(), \
            "full table's mb id %s differs from toc id mb %s" % (
            itable.getMusicBrainzDiscId(), ittoc.getMusicBrainzDiscId())
        assert itable.getAccurateRipURL() == ittoc.getAccurateRipURL(), \
            "full table's AR URL %s differs from toc AR URL %s" % (
            itable.getAccurateRipURL(), ittoc.getAccurateRipURL())

        outdir = self.options.output_directory or os.getcwd()
        profile = encode.PROFILES[self.options.profile]()
        extension = profile.extension

        # result
        res = result.RipResult()
        res.offset = int(self.options.offset)
        res.toctable = itable
        res.artist = metadata and metadata.artist or 'Unknown Artist'
        res.title = metadata and metadata.title or 'Unknown Title'
        _, res.vendor, res.model, __ = cdio.Device(device).get_hwinfo()

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
            htoapath = getPath(outdir, self.options.track_template, metadata, mbdiscid, 0) + '.' + extension
            dirname = os.path.dirname(htoapath)
            if not os.path.exists(dirname):
                os.makedirs(dirname)

            htoalength = stop - start
            if not os.path.exists(htoapath):
                print 'Ripping track %d: %s' % (0, os.path.basename(htoapath))
                t = cdparanoia.ReadVerifyTrackTask(htoapath, ittoc,
                    start, stop - 1,
                    offset=int(self.options.offset),
                    device=self.parentCommand.options.device,
                    profile=profile,
                    taglist=getTagList(metadata, 0))
                function(runner, t)

                if t.checksum is not None:
                    print 'Checksums match for track %d' % 0
                else:
                    print 'ERROR: checksums did not match for track %d' % 0
                print 'Peak level: %.2f %%' % (t.peak * 100.0, )
                if t.peak == 0.0:
                    print 'HTOA is completely silent'
                # overlay this rip onto the Table
            itable.setFile(1, 0, htoapath, htoalength, 0)


        for i, track in enumerate(itable.tracks):
            # FIXME: rip data tracks differently
            if not track.audio:
                print 'Skipping data track %d' % (i + 1, )
                # FIXME: make it work for now
                track.indexes[1].relative = 0
                continue

            trackResult = result.TrackResult()
            res.tracks.append(trackResult)

            path = getPath(outdir, self.options.track_template, metadata, mbdiscid, i + 1) + '.' + extension
            trackResult.number = i + 1
            trackResult.filename = path

            dirname = os.path.dirname(path)
            if not os.path.exists(dirname):
                os.makedirs(dirname)

            # FIXME: optionally allow overriding reripping
            if not os.path.exists(path):
                print 'Ripping track %d of %d: %s' % (
                    i + 1, len(itable.tracks), os.path.basename(path))
                t = cdparanoia.ReadVerifyTrackTask(path, ittoc,
                    ittoc.getTrackStart(i + 1),
                    ittoc.getTrackEnd(i + 1),
                    offset=int(self.options.offset),
                    device=self.parentCommand.options.device,
                    profile=profile,
                    taglist=getTagList(metadata, i + 1))
                t.description = 'Reading Track %d' % (i + 1)
                function(runner, t)
                if t.checksum:
                    print 'Checksums match for track %d' % (i + 1)
                else:
                    print 'ERROR: checksums did not match for track %d' % (i + 1)
                trackResult.testcrc = t.testchecksum
                trackResult.copycrc = t.copychecksum
                trackResult.peak = t.peak
                trackResult.quality = t.quality
                trackResult.pregap = itable.tracks[i].getPregap()

                print 'Peak level: %.2f %%' % (math.sqrt(t.peak) * 100.0, )
                print 'Rip quality: %.2f %%' % (t.quality * 100.0, )

            # overlay this rip onto the Table
            itable.setFile(i + 1, 1, path, ittoc.getTrackLength(i + 1), i + 1)


        ### write disc files
        discName = getPath(outdir, self.options.disc_template, metadata, mbdiscid, i)
        dirname = os.path.dirname(discName)
        if not os.path.exists(dirname):
            os.makedirs(dirname)

        # write .cue file
        assert itable.canCue()
        cuePath = '%s.cue' % discName
        handle = open(cuePath, 'w')
        # FIXME: do we always want utf-8 ?
        handle.write(itable.cue().encode('utf-8'))
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
            if not track.audio:
                continue

            path = getPath(outdir, self.options.track_template, metadata,
                mbdiscid, i + 1) + '.' + extension
            u = u'#EXTINF:%d,%s\n' % (
                itable.getTrackLength(i + 1) / common.FRAMES_PER_SECOND,
                os.path.basename(path))
            handle.write(u.encode('utf-8'))
            u = '%s\n' % os.path.basename(path)
            handle.write(u.encode('utf-8'))
        handle.close()

        # verify using accuraterip
        url = ittoc.getAccurateRipURL()
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
        for i, csum in enumerate(cuetask.checksums):
            trackResult = res.tracks[i]
            trackResult.accuripCRC = csum

            status = 'rip NOT accurate'

            confidence = None

            # match against each response's checksum
            for j, r in enumerate(responses or []):
                if "%08x" % csum == r.checksums[i]:
                    if not response:
                        response = r
                    else:
                        assert r == response, \
                            "checksum %s for %d matches wrong response %d, "\
                            "checksum %s" % (
                                csum, i + 1, j + 1, response.checksums[i])
                    status = 'rip accurate    '
                    trackResult.accurip = True
                    # FIXME: maybe checksums should be ints
                    trackResult.accuripDatabaseCRC = int(response.checksums[i], 16)
                    # arsum = csum
                    confidence = response.confidences[i]
                    trackResult.accuripDatabaseConfidence = confidence

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
                i + 1, status, c, csum, ar)

        # write log file
        discName = getPath(outdir, self.options.disc_template, metadata, mbdiscid, i)
        logPath = '%s.log' % discName
        logger = result.getLogger()
        handle = open(logPath, 'w')
        handle.write(logger.log(res).encode('utf-8'))
        handle.close()

class CD(logcommand.LogCommand):
    summary = "handle CD's"

    subCommandClasses = [Rip, ]

    def addOptions(self):
        self.parser.add_option('-d', '--device',
            action="store", dest="device",
            help="CD-DA device")
 
    def handleOptions(self, options):
        if not options.device:
            drives = drive.getAllDevicePaths()
            if not drives:
                self.error('No CD-DA drives found!')
                return 3
        
            # pick the first
            self.options.device = drives[0]

        # this can be a symlink to another device
        self.options.device = os.path.realpath(self.options.device)
