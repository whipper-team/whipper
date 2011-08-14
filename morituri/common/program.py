# -*- Mode: Python; test-case-name: morituri.test.test_common_program -*-
# vi:si:et:sw=4:sts=4:ts=4

# Morituri - for those about to RIP

# Copyright (C) 2009, 2010, 2011 Thomas Vander Stichele

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

"""
Common functionality and class for all programs using morituri.
"""

import os
import urlparse
import time

from morituri.common import common, log
from morituri.result import result
from morituri.program import cdrdao, cdparanoia
from morituri.image import image

class MusicBrainzException(Exception):
    def __init__(self, exc):
        self.args = (exc, )
        self.exception = exc

class TrackMetadata(object):
    artist = None
    title = None
    duration = None # in ms

class DiscMetadata(object):
    """
    @param release: earliest release date, in YYYY-MM-DD
    @type  release: unicode
    """
    artist = None
    sortName = None
    title = None
    various = False
    tracks = None
    release = None

    mbid = None
    mbidArtist = None

    def __init__(self):
        self.tracks = []

def filterForPath(text):
    return "-".join(text.split("/"))

def getMetadata(release):
    """
    @type  release: L{musicbrainz2.model.Release}

    @rtype: L{DiscMetadata} or None
    """
    log.debug('program', 'getMetadata for release id %r',
        release.getId())
    if not release.getId():
        log.warning('program', 'No id for release %r', release) 
        return None

    assert release.id, 'Release does not have an id'

    metadata = DiscMetadata()

    isSingleArtist = release.isSingleArtistRelease()
    metadata.various = not isSingleArtist
    metadata.title = release.title
    # getUniqueName gets disambiguating names like Muse (UK rock band)
    metadata.artist = release.artist.name
    metadata.sortName = release.artist.sortName
    metadata.release = release.getEarliestReleaseDate()

    metadata.mbid = urlparse.urlparse(release.id)[2].split("/")[-1]
    metadata.mbidArtist = urlparse.urlparse(release.artist.id)[2].split("/")[-1]


    duration = 0

    for t in release.tracks:
        track = TrackMetadata()
        track.duration = t.duration
        duration += t.duration
        if isSingleArtist or t.artist == None:
            track.artist = metadata.artist
            track.sortName = metadata.sortName
            track.mbidArtist = metadata.mbidArtist
        else:
            # various artists discs can have tracks with no artist
            track.artist = t.artist and t.artist.name or release.artist.name
            track.sortName = t.artist.sortName
            track.mbidArtist = urlparse.urlparse(t.artist.id)[2].split("/")[-1] 

        track.title = t.title
        track.mbid = urlparse.urlparse(t.id)[2].split("/")[-1]
        metadata.tracks.append(track)

    metadata.duration = duration

    return metadata


def musicbrainz(discid):
    """
    @rtype: list of L{DiscMetadata}
    """
    log.debug('musicbrainz', 'looking up results for discid %r', discid)
    #import musicbrainz2.disc as mbdisc
    import musicbrainz2.webservice as mbws

    results = []

    # Setup a Query object.
    service = mbws.WebService()
    query = mbws.Query(service)


    # Query for all discs matching the given DiscID.
    # FIXME: let mbws.WebServiceError go through for now
    try:
        rfilter = mbws.ReleaseFilter(discId=discid)
        results = query.getReleases(rfilter)
    except mbws.WebServiceError, e:
        raise MusicBrainzException(e)

    # No disc matching this DiscID has been found.
    if len(results) == 0:
        return None

    log.debug('musicbrainz', 'found %d results for discid %r', len(results),
        discid)

    # Display the returned results to the user.
    ret = []

    for result in results:
        release = result.release
        log.debug('program', 'result %r: artist %r, title %r' % (
            release, release.artist.getName(), release.title))
        # The returned release object only contains title and artist, but no
        # tracks.  Query the web service once again to get all data we need.
        try:
            inc = mbws.ReleaseIncludes(artist=True, tracks=True,
                releaseEvents=True)
            # Arid - Under the Cold Street Lights has getId() None
            if release.getId():
                release = query.getReleaseById(release.getId(), inc)
        except mbws.WebServiceError, e:
            raise MusicBrainzException(e)

        md = getMetadata(release)
        if md:
            log.debug('program', 'duration %r', md.duration)
            ret.append(md)


    return ret

class Program(log.Loggable):
    """
    I maintain program state and functionality.

    @ivar metadata:
    @type metadata: L{DiscMetadata}
    @ivar result:   the rip's result
    @type result:   L{result.RipResult}
    @type outdir:   unicode
    """

    cuePath = None
    logPath = None
    metadata = None
    outdir = None
    result = None

    def _getTableCachePath(self):
        path = os.path.join(os.path.expanduser('~'), '.morituri', 'cache',
            'table')
        return path

    def _getResultCachePath(self):
        path = os.path.join(os.path.expanduser('~'), '.morituri', 'cache',
            'result')
        return path

    def loadDevice(self, device):
        """
        Load the given device.
        """
        os.system('eject -t %s' % device)

    def ejectDevice(self, device):
        """
        Eject the given device.
        """
        os.system('eject %s' % device)

    def unmountDevice(self, device):
        """
        Unmount the given device if it is mounted, as happens with automounted
        data tracks.

        If the given device is a symlink, the target will be checked.
        """
        device = os.path.realpath(device)
        self.debug('possibly unmount real path %r' % device)
        proc = open('/proc/mounts').read()
        if device in proc:
            print 'Device %s is mounted, unmounting' % device
            os.system('umount %s' % device)
        
    def getTable(self, runner, cddbdiscid, device):
        """
        Retrieve the Table either from the cache or the drive.

        @rtype: L{table.Table}
        """
        path = self._getTableCachePath()

        pcache = common.PersistedCache(path)
        ptable = pcache.get(cddbdiscid)

        if not ptable.object:
            t = cdrdao.ReadTableTask(device=device)
            runner.run(t)
            ptable.persist(t.table)
        itable = ptable.object
        assert itable.hasTOC()

        self.result.table = itable

        return itable

    def getRipResult(self, cddbdiscid):
        """
        Retrieve the persistable RipResult either from our cache (from a
        previous, possibly aborted rip), or return a new one.

        @rtype: L{result.RipResult}
        """
        assert self.result is None

        path = self._getResultCachePath()

        pcache = common.PersistedCache(path)
        presult = pcache.get(cddbdiscid)

        if not presult.object:
            presult.object = result.RipResult()
            presult.persist(self.result)

        self.result = presult.object
        self._presult = presult

        return self.result

    def saveRipResult(self):
        self._presult.persist()

    def getPath(self, outdir, template, mbdiscid, i):
        """
        Based on the template, get a complete path for the given track,
        minus extension.
        Also works for the disc name, using disc variables for the template.

        @param outdir:   the directory where to write the files
        @type  outdir:   unicode
        @param template: the template for writing the file
        @type  template: unicode
        @param i:        track number (0 for HTOA)
        @type  i:        int

        @rtype: unicode
        """
        assert type(outdir) is unicode, "%r is not unicode" % outdir
        assert type(template) is unicode, "%r is not unicode" % template

        # the template is similar to grip, except for %s/%S

        # returns without extension

        v = {}

        v['t'] = '%02d' % i

        # default values
        v['A'] = 'Unknown Artist'
        v['d'] = mbdiscid

        v['a'] = v['A']
        if i == 0:
            v['n'] = 'Hidden Track One Audio'
        else:
            v['n'] = 'Unknown Track %d' % i


        if self.metadata:
            v['A'] = filterForPath(self.metadata.artist)
            v['S'] = filterForPath(self.metadata.sortName)
            v['d'] = filterForPath(self.metadata.title)
            if i > 0:
                try:
                    v['a'] = filterForPath(self.metadata.tracks[i - 1].artist)
                    v['s'] = filterForPath(self.metadata.tracks[i - 1].sortName)
                    v['n'] = filterForPath(self.metadata.tracks[i - 1].title)
                except IndexError, e:
                    print 'ERROR: no track %d found, %r' % (i, e)
                    raise
            else:
                # htoa defaults to disc's artist
                v['a'] = filterForPath(self.metadata.artist)

        import re
        template = re.sub(r'%(\w)', r'%(\1)s', template)

        return os.path.join(outdir, template % v)

    def getCDDB(self, cddbdiscid):
        """
        @param cddbdiscid: list of id, tracks, offsets, seconds

        @rtype: str
        """
        # FIXME: convert to nonblocking?
        import CDDB
        code, md = CDDB.query(cddbdiscid) 
        self.debug('CDDB query result: %r, %r', code, md)
        if code == 200:
            return md['title']

        return None


    def getMusicBrainz(self, ittoc, mbdiscid):
        # look up disc on musicbrainz
        self.debug('MusicBrainz submit url: %r', 
            ittoc.getMusicBrainzSubmitURL())
        ret = None

        metadatas = None
        for i in range(0, 4):
            try:
                metadatas = musicbrainz(mbdiscid)
            except MusicBrainzException, e:
                print "Warning:", e
                time.sleep(5)
                continue

        if not metadatas:
            print "Error:", e
            print 'Continuing without metadata'

        if metadatas:
            print 'Disc duration: %s' % common.formatTime(
                ittoc.duration() / 1000.0)
            print
            print 'Matching releases:'
            deltas = {}
            for metadata in metadatas:

                print 'Artist  : %s' % metadata.artist.encode('utf-8')
                print 'Title   : %s' % metadata.title.encode('utf-8')
                print 'Duration: %s' % common.formatTime(
                    metadata.duration / 1000.0)

                delta = abs(metadata.duration - ittoc.duration())
                if not delta in deltas:
                    deltas[delta] = []
                deltas[delta].append(metadata)

            # Select the release that most closely matches the duration.
            lowest = min(deltas.keys())

            # If we have multiple, make sure they match
            metadatas = deltas[lowest]
            if len(metadatas) > 1:
                artist = metadatas[0].artist
                title = metadatas[0].title
                for metadata in metadatas:
                    assert artist == metadata.artist
                    assert title == metadata.title

                if (len(deltas.keys()) > 1):
                    print
                    print 'Picked closest match in duration.'
                    print 'Others may be wrong in musicbrainz, please correct.'
                    print 'Artist : %s' % artist
                    print 'Title :  %s' % title

            # Select one of the returned releases. We just pick the first one.
            ret = metadatas[0]
        else:
            print 'Submit this disc to MusicBrainz at the above URL.'
            ret = None

        print
        return ret


    def getTagList(self, number):
        """
        Based on the metadata, get a gst.TagList for the given track.

        @param number:   track number (0 for HTOA)
        @type  number:   int

        @rtype: L{gst.TagList}
        """
        trackArtist = u'Unknown Artist'
        albumArtist = u'Unknown Artist'
        disc = u'Unknown Disc'
        title = u'Unknown Track'

        if self.metadata:
            trackArtist = self.metadata.artist
            albumArtist = self.metadata.artist
            disc = self.metadata.title
            mbidAlbum = self.metadata.mbid
            mbidTrackAlbum = self.metadata.mbidArtist

            if number > 0:
                try:
                    trackArtist = self.metadata.tracks[number - 1].artist
                    title = self.metadata.tracks[number - 1].title
                    mbidTrack = self.metadata.tracks[number - 1].mbid
                    mbidTrackArtist = self.metadata.tracks[number - 1].mbidArtist
                except IndexError, e:
                    print 'ERROR: no track %d found, %r' % (number, e)
                    raise
            else:
                # htoa defaults to disc's artist
                title = 'Hidden Track One Audio'

        # here to avoid import gst eating our options
        import gst

        ret = gst.TagList()

        # gst-python 0.10.15.1 does not handle unicode -> utf8 string conversion
        # see http://bugzilla.gnome.org/show_bug.cgi?id=584445
        if self.metadata and self.metadata.various:
            ret["album-artist"] = albumArtist.encode('utf-8')
        ret[gst.TAG_ARTIST] = trackArtist.encode('utf-8')
        ret[gst.TAG_TITLE] = title.encode('utf-8')
        ret[gst.TAG_ALBUM] = disc.encode('utf-8')

        # gst-python 0.10.15.1 does not handle tags that are UINT
        # see gst-python commit 26fa6dd184a8d6d103eaddf5f12bd7e5144413fb
        # FIXME: no way to compare against 'master' version after 0.10.15
        if gst.pygst_version >= (0, 10, 15):
            ret[gst.TAG_TRACK_NUMBER] = number
        if self.metadata:
            # works, but not sure we want this
            # if gst.pygst_version >= (0, 10, 15):
            #     ret[gst.TAG_TRACK_COUNT] = len(self.metadata.tracks)
            # hack to get a GstDate which we cannot instantiate directly in
            # 0.10.15.1
            # FIXME: The dates are strings and must have the format 'YYYY',
            # 'YYYY-MM' or 'YYYY-MM-DD'.
            # GstDate expects a full date, so default to Jan and 1st if MM and DD
            # are missing
            date = self.metadata.release
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
            
            # no musicbrainz info for htoa tracks
            if number > 0:
                ret["musicbrainz-trackid"] = mbidTrack
                ret["musicbrainz-artistid"] = mbidTrackArtist
                ret["musicbrainz-albumid"] = mbidAlbum
                ret["musicbrainz-albumartistid"] = mbidTrackAlbum
            
        # FIXME: gst.TAG_ISRC 

        return ret

    def getHTOA(self):
        """
        Check if we have hidden track one audio.

        @returns: tuple of (start, stop), or None
        """
        track = self.result.table.tracks[0]
        try:
            index = track.getIndex(0)
        except KeyError:
            return None

        start = index.absolute
        stop = track.getIndex(1).absolute - 1
        return (start, stop)

    def verifyTrack(self, runner, trackResult):
        # here to avoid import gst eating our options
        from morituri.common import checksum

        t = checksum.CRC32Task(trackResult.filename)

        runner.run(t)

        return trackResult.testcrc == t.checksum

    def ripTrack(self, runner, trackResult, offset, device, profile, taglist,
        what=None):
        """
        @param trackResult: the object to store information in.
        @type  trackResult: L{result.TrackResult}
        @param number:      track number (1-based)
        @type  number:      int
        """
        if trackResult.number == 0:
            start, stop = self.getHTOA()
        else:
            start = self.result.table.getTrackStart(trackResult.number)
            stop = self.result.table.getTrackEnd(trackResult.number)

        dirname = os.path.dirname(trackResult.filename)
        if not os.path.exists(dirname):
            os.makedirs(dirname)

        if not what:
            what='track %d' % (trackResult.number, )

        t = cdparanoia.ReadVerifyTrackTask(trackResult.filename,
            self.result.table, start, stop,
            offset=offset,
            device=device,
            profile=profile,
            taglist=taglist,
            what=what)

        runner.run(t)

        trackResult.testcrc = t.testchecksum
        trackResult.copycrc = t.copychecksum
        trackResult.peak = t.peak
        trackResult.quality = t.quality

    def retagImage(self, runner, taglists):
        cueImage = image.Image(self.cuePath)
        t = image.ImageRetagTask(cueImage, taglists)
        runner.run(t)

    def verifyImage(self, runner, responses):
        """
        Verify our image against the given AccurateRip responses.

        Needs an initialized self.result.
        Will set accurip and friends on each TrackResult.
        """

        self.debug('verifying Image against %d AccurateRip responses',
            len(responses or []))

        cueImage = image.Image(self.cuePath)
        verifytask = image.ImageVerifyTask(cueImage)
        cuetask = image.AccurateRipChecksumTask(cueImage)
        runner.run(verifytask)
        runner.run(cuetask)

        self._verifyImageWithChecksums(responses, cuetask.checksums)

    def _verifyImageWithChecksums(self, responses, checksums):
        # loop over tracks to set our calculated AccurateRip CRC's
        for i, csum in enumerate(checksums):
            trackResult = self.result.getTrackResult(i + 1)
            trackResult.ARCRC = csum


        if not responses:
            self.warning('No AccurateRip responses, cannot verify.')
            return

        # now loop to match responses
        for i, csum in enumerate(checksums):
            trackResult = self.result.getTrackResult(i + 1)

            confidence = None
            response = None

            # match against each response's checksum for this track
            for j, r in enumerate(responses):
                if "%08x" % csum == r.checksums[i]:
                    response = r
                    self.debug(
                        "Track %02d matched response %d of %d in "
                        "AccurateRip database",
                        i + 1, j + 1, len(responses))
                    trackResult.accurip = True
                    # FIXME: maybe checksums should be ints
                    trackResult.ARDBCRC = int(r.checksums[i], 16)
                    # arsum = csum
                    confidence = r.confidences[i]
                    trackResult.ARDBConfidence = confidence

            if not trackResult.accurip:
                self.warning("Track %02d: not matched in AccurateRip database",
                    i + 1)

            # I have seen AccurateRip responses with 0 as confidence
            # for example, Best of Luke Haines, disc 1, track 1
            maxConfidence = -1
            maxResponse = None
            for r in responses:
                if r.confidences[i] > maxConfidence:
                    maxConfidence = r.confidences[i]
                    maxResponse = r

            self.debug('Track %02d: found max confidence %d' % (
                i + 1, maxConfidence))
            trackResult.ARDBMaxConfidence = maxConfidence
            if not response:
                self.warning('Track %02d: none of the responses matched.',
                    i + 1)
                trackResult.ARDBCRC = int(
                    maxResponse.checksums[i], 16)
            else:
                trackResult.ARDBCRC = int(response.checksums[i], 16)

    def getAccurateRipResults(self):
        """
        @rtype: list of str
        """
        res = []

        # loop over tracks
        for i, trackResult in enumerate(self.result.tracks):
            status = 'rip NOT accurate'

            if trackResult.accurip:
                    status = 'rip accurate    '

            c = "(not found)            "
            ar = ", DB [notfound]"
            if trackResult.ARDBMaxConfidence:
                c = "(max confidence    %3d)" % trackResult.ARDBMaxConfidence
                if trackResult.ARDBConfidence is not None:
                    if trackResult.ARDBConfidence \
                            < trackResult.ARDBMaxConfidence:
                        c = "(confidence %3d of %3d)" % (
                            trackResult.ARDBConfidence,
                            trackResult.ARDBMaxConfidence)

                ar = ", DB [%08x]" % trackResult.ARDBCRC
            # htoa tracks (i == 0) do not have an ARCRC
            if trackResult.ARCRC is None:
                assert trackResult.number == 0, \
                    'no trackResult.ARCRC on non-HTOA track'
                res.append("Track  0: unknown          (not tracked)")
            else:
                res.append("Track %2d: %s %s [%08x]%s" % (
                    trackResult.number, status, c, trackResult.ARCRC, ar))

        return res

    def writeCue(self, discName):
        assert self.result.table.canCue()
        cuePath = '%s.cue' % discName
        self.debug('write .cue file to %s', cuePath)
        handle = open(cuePath, 'w')
        # FIXME: do we always want utf-8 ?
        handle.write(self.result.table.cue().encode('utf-8'))
        handle.close()

        self.cuePath = cuePath

        return cuePath

    def writeLog(self, discName, logger):
        logPath = '%s.log' % discName
        handle = open(logPath, 'w')
        handle.write(logger.log(self.result).encode('utf-8'))
        handle.close()

        self.logPath = logPath

        return logPath
