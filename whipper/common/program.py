# -*- Mode: Python; test-case-name: whipper.test.test_common_program -*-
# vi:si:et:sw=4:sts=4:ts=4

# Copyright (C) 2009, 2010, 2011 Thomas Vander Stichele

# This file is part of whipper.
#
# whipper is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# whipper is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with whipper.  If not, see <http://www.gnu.org/licenses/>.

"""
Common functionality and class for all programs using whipper.
"""

import musicbrainzngs
import re
import os
import sys
import time

from whipper.common import accurip, cache, checksum, common, mbngs, path
from whipper.program import cdrdao, cdparanoia
from whipper.image import image
from whipper.extern import freedb
from whipper.extern.task import task

import logging
logger = logging.getLogger(__name__)


# FIXME: should Program have a runner ?


class Program:
    """
    I maintain program state and functionality.

    @ivar metadata:
    @type metadata: L{mbngs.DiscMetadata}
    @ivar result:   the rip's result
    @type result:   L{result.RipResult}
    @type outdir:   unicode
    @type config:   L{whipper.common.config.Config}
    """

    cuePath = None
    logPath = None
    metadata = None
    outdir = None
    result = None

    _stdout = None

    def __init__(self, config, record=False, stdout=sys.stdout):
        """
        @param record: whether to record results of API calls for playback.
        """
        self._record = record
        self._cache = cache.ResultCache()
        self._stdout = stdout
        self._config = config

        d = {}

        for key, default in list({
            'fat': True,
            'special': False
        }.items()):
            value = None
            value = self._config.getboolean('main', 'path_filter_' + key)
            if value is None:
                value = default

            d[key] = value

        self._filter = path.PathFilter(**d)

    def setWorkingDirectory(self, workingDirectory):
        if workingDirectory:
            logger.info('Changing to working directory %s' % workingDirectory)
            os.chdir(workingDirectory)

    def getFastToc(self, runner, device):
        """Retrieve the normal TOC table from the drive.
        Also warn about buggy cdrdao versions.
        """
        from pkg_resources import parse_version as V
        version = cdrdao.getCDRDAOVersion()
        if V(version) < V('1.2.3rc2'):
            sys.stdout.write('Warning: cdrdao older than 1.2.3 has a '
                             'pre-gap length bug.\n'
                             'See http://sourceforge.net/tracker/?func=detail&aid=604751&group_id=2171&atid=102171\n')  # noqa: E501
        toc = cdrdao.ReadTOCTask(device).table
        assert toc.hasTOC()
        return toc

    def getTable(self, runner, cddbdiscid, mbdiscid, device, offset,
                 out_bpath, out_fpath):
        """
        Retrieve the Table either from the cache or the drive.

        @rtype: L{table.Table}
        """
        tcache = cache.TableCache()
        ptable = tcache.get(cddbdiscid, mbdiscid)
        itable = None
        tdict = {}

        # Ignore old cache, since we do not know what offset it used.
        if isinstance(ptable.object, dict):
            tdict = ptable.object

            if offset in tdict:
                itable = tdict[offset]

        if not itable:
            logger.debug('getTable: cddbdiscid %s, mbdiscid %s not '
                         'in cache for offset %s, reading table' % (
                             cddbdiscid, mbdiscid, offset))
            t = cdrdao.ReadTableTask(device, out_bpath, out_fpath)
            itable = t.table
            tdict[offset] = itable
            ptable.persist(tdict)
            logger.debug('getTable: read table %r' % itable)
        else:
            logger.debug('getTable: cddbdiscid %s, mbdiscid %s in cache '
                         'for offset %s' % (cddbdiscid, mbdiscid, offset))
            logger.debug('getTable: loaded table %r' % itable)

        assert itable.hasTOC()

        self.result.table = itable

        logger.debug('getTable: returning table with mb id %s' %
                     itable.getMusicBrainzDiscId())
        return itable

    def getRipResult(self, cddbdiscid):
        """
        Retrieve the persistable RipResult either from our cache (from a
        previous, possibly aborted rip), or return a new one.

        @rtype: L{result.RipResult}
        """
        assert self.result is None

        self._presult = self._cache.getRipResult(cddbdiscid)
        self.result = self._presult.object

        return self.result

    def saveRipResult(self):
        self._presult.persist()

    def addDisambiguation(self, template_part, metadata):
        "Add disambiguation to template path part string."
        if metadata.catalogNumber:
            template_part += ' (%s)' % metadata.catalogNumber
        elif metadata.barcode:
            template_part += ' (%s)' % metadata.barcode
        return template_part

    def getPath(self, outdir, template, mbdiscid, metadata, track_number=None):
        """
        Return disc or track path relative to outdir according to
        template. Track paths do not include extension.

        Tracks are named according to the track template, filling in
        the variables and adding the file extension. Variables
        exclusive to the track template are:
          - %t: track number
          - %a: track artist
          - %n: track title
          - %s: track sort name

        Disc files (.cue, .log, .m3u) are named according to the disc
        template, filling in the variables and adding the file
        extension. Variables for both disc and track template are:
          - %A: album artist
          - %S: album sort name
          - %d: disc title
          - %y: release year
          - %r: release type, lowercase
          - %R: Release type, normal case
          - %x: audio extension, lowercase
          - %X: audio extension, uppercase
        """
        assert isinstance(outdir, unicode), "%r is not unicode" % outdir
        assert isinstance(template, unicode), "%r is not unicode" % template
        v = {}
        v['A'] = 'Unknown Artist'
        v['d'] = mbdiscid  # fallback for title
        v['r'] = 'unknown'
        v['R'] = 'Unknown'
        v['B'] = ''  # barcode
        v['C'] = ''  # catalog number
        v['x'] = 'flac'
        v['X'] = v['x'].upper()
        v['y'] = '0000'
        if track_number is not None:
            v['a'] = v['A']
            v['t'] = '%02d' % track_number
            if track_number == 0:
                v['n'] = 'Hidden Track One Audio'
            else:
                v['n'] = 'Unknown Track %d' % track_number

        if metadata:
            release = metadata.release or '0000'
            v['y'] = release[:4]
            v['A'] = self._filter.filter(metadata.artist)
            v['S'] = self._filter.filter(metadata.sortName)
            v['d'] = self._filter.filter(metadata.title)
            v['B'] = metadata.barcode
            v['C'] = metadata.catalogNumber
            if metadata.releaseType:
                v['R'] = metadata.releaseType
                v['r'] = metadata.releaseType.lower()
            if track_number > 0:
                v['a'] = self._filter.filter(
                    metadata.tracks[track_number - 1].artist)
                v['s'] = self._filter.filter(
                    metadata.tracks[track_number - 1].sortName)
                v['n'] = self._filter.filter(
                    metadata.tracks[track_number - 1].title)
            elif track_number == 0:
                # htoa defaults to disc's artist
                v['a'] = self._filter.filter(metadata.artist)

        template = re.sub(r'%(\w)', r'%(\1)s', template)
        return os.path.join(outdir, template % v)

    def getCDDB(self, cddbdiscid):
        """
        @param cddbdiscid: list of id, tracks, offsets, seconds

        @rtype: str
        """
        # FIXME: convert to nonblocking?
        try:
            md = freedb.perform_lookup(cddbdiscid, 'freedb.freedb.org', 80)
            logger.debug('CDDB query result: %r', md)
            return [item['DTITLE'] for item in md if 'DTITLE' in item] or None

        except ValueError as e:
            self._stdout.write("WARNING: CDDB protocol error: %s\n" % e)

        except IOError as e:
            # FIXME: for some reason errno is a str ?
            if e.errno == 'socket error':
                self._stdout.write("WARNING: CDDB network error: %r\n" % (e, ))
            else:
                raise

        return None

    def getMusicBrainz(self, ittoc, mbdiscid, release=None, country=None,
                       prompt=False):
        """
        @type  ittoc: L{whipper.image.table.Table}
        """
        # look up disc on MusicBrainz
        self._stdout.write('Disc duration: %s, %d audio tracks\n' % (
            common.formatTime(ittoc.duration() / 1000.0),
            ittoc.getAudioTracks()))
        logger.debug('MusicBrainz submit url: %r',
                     ittoc.getMusicBrainzSubmitURL())
        ret = None

        metadatas = None
        e = None

        for _ in range(0, 4):
            try:
                metadatas = mbngs.musicbrainz(mbdiscid,
                                              country=country,
                                              record=self._record)
                break
            except mbngs.NotFoundException as e:
                logger.warning("release not found: %r" % (e, ))
                break
            except musicbrainzngs.NetworkError as e:
                logger.warning("network error: %r" % (e, ))
                break
            except mbngs.MusicBrainzException as e:
                logger.warning("musicbrainz exception: %r" % (e, ))
                time.sleep(5)
                continue

        if not metadatas:
            self._stdout.write('Continuing without metadata\n')

        if metadatas:
            deltas = {}

            self._stdout.write('\nMatching releases:\n')

            for metadata in metadatas:
                self._stdout.write('\n')
                self._stdout.write('Artist  : %s\n' %
                                   metadata.artist.encode('utf-8'))
                self._stdout.write('Title   : %s\n' %
                                   metadata.title.encode('utf-8'))
                self._stdout.write('Duration: %s\n' %
                                   common.formatTime(metadata.duration /
                                                     1000.0))
                self._stdout.write('URL     : %s\n' % metadata.url)
                self._stdout.write('Release : %s\n' % metadata.mbid)
                self._stdout.write('Type    : %s\n' % metadata.releaseType)
                if metadata.barcode:
                    self._stdout.write("Barcode : %s\n" % metadata.barcode)
                if metadata.catalogNumber:
                    self._stdout.write("Cat no  : %s\n" %
                                       metadata.catalogNumber)

                delta = abs(metadata.duration - ittoc.duration())
                if delta not in deltas:
                    deltas[delta] = []
                deltas[delta].append(metadata)

            lowest = None

            if not release and len(metadatas) > 1:
                # Select the release that most closely matches the duration.
                lowest = min(list(deltas))

                if prompt:
                    guess = (deltas[lowest])[0].mbid
                    release = raw_input(
                        "\nPlease select a release [%s]: " % guess)

                    if not release:
                        release = guess

            if release:
                metadatas = [m for m in metadatas if m.url.endswith(release)]
                logger.debug('Asked for release %r, only kept %r',
                             release, metadatas)
                if len(metadatas) == 1:
                    self._stdout.write('\n')
                    self._stdout.write('Picked requested release id %s\n' %
                                       release)
                    self._stdout.write('Artist : %s\n' %
                                       metadatas[0].artist.encode('utf-8'))
                    self._stdout.write('Title :  %s\n' %
                                       metadatas[0].title.encode('utf-8'))
                elif not metadatas:
                    self._stdout.write(
                        "Requested release id '%s', "
                        "but none of the found releases match\n" % release)
                    return
            else:
                if lowest:
                    metadatas = deltas[lowest]

            # If we have multiple, make sure they match
            if len(metadatas) > 1:
                artist = metadatas[0].artist
                releaseTitle = metadatas[0].releaseTitle
                for i, metadata in enumerate(metadatas):
                    if not artist == metadata.artist:
                        logger.warning("artist 0: %r and artist %d: %r "
                                       "are not the same" % (
                                           artist, i, metadata.artist))
                    if not releaseTitle == metadata.releaseTitle:
                        logger.warning("title 0: %r and title %d: %r "
                                       "are not the same" % (
                                           releaseTitle, i,
                                           metadata.releaseTitle))

                if (not release and len(list(deltas)) > 1):
                    self._stdout.write('\n')
                    self._stdout.write('Picked closest match in duration.\n')
                    self._stdout.write('Others may be wrong in MusicBrainz, '
                                       'please correct.\n')
                    self._stdout.write('Artist : %s\n' %
                                       artist.encode('utf-8'))
                    self._stdout.write('Title :  %s\n' %
                                       metadatas[0].title.encode('utf-8'))

            # Select one of the returned releases. We just pick the first one.
            ret = metadatas[0]
        else:
            self._stdout.write(
                'Submit this disc to MusicBrainz at the above URL.\n')
            ret = None

        self._stdout.write('\n')
        return ret

    def getTagList(self, number):
        """
        Based on the metadata, get a dict of tags for the given track.

        @param number:   track number (0 for HTOA)
        @type  number:   int

        @rtype: dict
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
            mbDiscId = self.metadata.discid

            if number > 0:
                try:
                    track = self.metadata.tracks[number - 1]
                    trackArtist = track.artist
                    title = track.title
                    mbidTrack = track.mbid
                    mbidTrackArtist = track.mbidArtist
                except IndexError as e:
                    print('ERROR: no track %d found, %r' % (number, e))
                    raise
            else:
                # htoa defaults to disc's artist
                title = 'Hidden Track One Audio'

        tags = {}

        if self.metadata and not self.metadata.various:
            tags['ALBUMARTIST'] = albumArtist
        tags['ARTIST'] = trackArtist
        tags['TITLE'] = title
        tags['ALBUM'] = disc

        tags['TRACKNUMBER'] = u'%s' % number

        if self.metadata:
            if self.metadata.release is not None:
                tags['DATE'] = self.metadata.release

            if number > 0:
                tags['MUSICBRAINZ_TRACKID'] = mbidTrack
                tags['MUSICBRAINZ_ARTISTID'] = mbidTrackArtist
                tags['MUSICBRAINZ_ALBUMID'] = mbidAlbum
                tags['MUSICBRAINZ_ALBUMARTISTID'] = mbidTrackAlbum
                tags['MUSICBRAINZ_DISCID'] = mbDiscId

        # TODO/FIXME: ISRC tag

        return tags

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
        is_wave = not trackResult.filename.endswith('.flac')
        t = checksum.CRC32Task(trackResult.filename, is_wave=is_wave)

        try:
            runner.run(t)
        except task.TaskException as e:
            if isinstance(e.exception, common.MissingFrames):
                logger.warning('missing frames for %r' % trackResult.filename)
                return False
            else:
                raise

        ret = trackResult.testcrc == t.checksum
        logger.debug('verifyTrack: track result crc %r, '
                     'file crc %r, result %r',
                     trackResult.testcrc, t.checksum, ret)
        return ret

    def ripTrack(self, runner, trackResult, offset, device, taglist,
                 overread, what=None):
        """
        Ripping the track may change the track's filename as stored in
        trackResult.

        @param trackResult: the object to store information in.
        @type  trackResult: L{result.TrackResult}
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
            what = 'track %d' % (trackResult.number, )

        t = cdparanoia.ReadVerifyTrackTask(trackResult.filename,
                                           self.result.table, start,
                                           stop, overread,
                                           offset=offset,
                                           device=device,
                                           taglist=taglist,
                                           what=what)

        runner.run(t)

        logger.debug('ripped track')
        logger.debug('test speed %.3f/%.3f seconds' % (
            t.testspeed, t.testduration))
        logger.debug('copy speed %.3f/%.3f seconds' % (
            t.copyspeed, t.copyduration))
        trackResult.testcrc = t.testchecksum
        trackResult.copycrc = t.copychecksum
        trackResult.peak = t.peak
        trackResult.quality = t.quality
        trackResult.testspeed = t.testspeed
        trackResult.copyspeed = t.copyspeed
        # we want rerips to add cumulatively to the time
        trackResult.testduration += t.testduration
        trackResult.copyduration += t.copyduration

        if trackResult.filename != t.path:
            trackResult.filename = t.path
            logger.info('Filename changed to %r', trackResult.filename)

    def verifyImage(self, runner, table):
        """
        verify table against accuraterip and cue_path track lengths
        Verify our image against the given AccurateRip responses.

        Needs an initialized self.result.
        Will set accurip and friends on each TrackResult.

        Populates self.result.tracks with above TrackResults.
        """
        cueImage = image.Image(self.cuePath)
        # assigns track lengths
        verifytask = image.ImageVerifyTask(cueImage)
        runner.run(verifytask)
        if verifytask.exception:
            logger.error(verifytask.exceptionMessage)
            return False

        responses = accurip.get_db_entry(table.accuraterip_path())
        logger.info('%d AccurateRip response(s) found' % len(responses))

        checksums = accurip.calculate_checksums([
            os.path.join(os.path.dirname(self.cuePath), t.indexes[1].path)
            for t in [t for t in cueImage.cue.table.tracks if t.number != 0]
        ])
        if not (checksums and any(checksums['v1']) and any(checksums['v2'])):
            return False
        return accurip.verify_result(self.result, responses, checksums)

    def write_m3u(self, discname):
        m3uPath = common.truncate_filename(discname + '.m3u')
        with open(m3uPath, 'w') as f:
            f.write(u'#EXTM3U\n'.encode('utf-8'))
            for track in self.result.tracks:
                if not track.filename:
                    # false positive htoa
                    continue
                if track.number == 0:
                    length = (self.result.table.getTrackStart(1) /
                              common.FRAMES_PER_SECOND)
                else:
                    length = (self.result.table.getTrackLength(track.number) /
                              common.FRAMES_PER_SECOND)

                target_path = common.getRelativePath(track.filename, m3uPath)
                u = u'#EXTINF:%d,%s\n' % (length, target_path)
                f.write(u.encode('utf-8'))
                u = '%s\n' % target_path
                f.write(u.encode('utf-8'))

    def writeCue(self, discName):
        assert self.result.table.canCue()
        cuePath = common.truncate_filename(discName + '.cue')
        logger.debug('write .cue file to %s', cuePath)
        handle = open(cuePath, 'w')
        # FIXME: do we always want utf-8 ?
        handle.write(self.result.table.cue(cuePath).encode('utf-8'))
        handle.close()

        self.cuePath = cuePath

        return cuePath

    def writeLog(self, discName, logger):
        logPath = common.truncate_filename(discName + '.log')
        handle = open(logPath, 'w')
        log = logger.log(self.result)
        handle.write(log.encode('utf-8'))
        handle.close()

        self.logPath = logPath

        return logPath
