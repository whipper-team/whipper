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

import argparse
import os
import glob
import urllib2
import socket
import sys

import gobject
gobject.threads_init()

from morituri.command.basecommand import BaseCommand
from morituri.common import (
    accurip, common, config, drive, program, task
)
from morituri.program import cdrdao, cdparanoia, utils
from morituri.result import result

import logging
logger = logging.getLogger(__name__)


SILENT = 1e-10
MAX_TRIES = 5

DEFAULT_TRACK_TEMPLATE = u'%r/%A - %d/%t. %a - %n'
DEFAULT_DISC_TEMPLATE = u'%r/%A - %d/%A - %d'

TEMPLATE_DESCRIPTION = '''
Tracks are named according to the track template, filling in the variables
and adding the file extension.  Variables exclusive to the track template are:
 - %t: track number
 - %a: track artist
 - %n: track title
 - %s: track sort name

Disc files (.cue, .log, .m3u) are named according to the disc template,
filling in the variables and adding the file extension. Variables for both
disc and track template are:
 - %A: album artist
 - %S: album sort name
 - %d: disc title
 - %y: release year
 - %r: release type, lowercase
 - %R: Release type, normal case
 - %x: audio extension, lowercase
 - %X: audio extension, uppercase

'''


class _CD(BaseCommand):

    """
    @type program: L{program.Program}
    @ivar eject:   whether to eject the drive after completing
    """

    eject = True

    @staticmethod
    def add_arguments(parser):
        # FIXME: have a cache of these pickles somewhere
        parser.add_argument('-T', '--toc-pickle',
            action="store", dest="toc_pickle",
            help="pickle to use for reading and writing the TOC")
        parser.add_argument('-R', '--release-id',
            action="store", dest="release_id",
            help="MusicBrainz release id to match to (if there are multiple)")
        parser.add_argument('-p', '--prompt',
            action="store_true", dest="prompt",
            help="Prompt if there are multiple matching releases")
        parser.add_argument('-c', '--country',
            action="store", dest="country",
            help="Filter releases by country")


    def do(self):
        self.config = config.Config()
        self.program = program.Program(self.config,
            record=self.options.record,
            stdout=sys.stdout)
        self.runner = task.SyncRunner()

        # if the device is mounted (data session), unmount it
        #self.device = self.parentCommand.options.device
        self.device = self.options.device
        sys.stdout.write('Checking device %s\n' % self.device)

        utils.load_device(self.device)
        utils.unmount_device(self.device)

        # first, read the normal TOC, which is fast
        self.ittoc = self.program.getFastToc(self.runner,
            self.options.toc_pickle,
            self.device)

        # already show us some info based on this
        self.program.getRipResult(self.ittoc.getCDDBDiscId())
        sys.stdout.write("CDDB disc id: %s\n" % self.ittoc.getCDDBDiscId())
        self.mbdiscid = self.ittoc.getMusicBrainzDiscId()
        sys.stdout.write("MusicBrainz disc id %s\n" % self.mbdiscid)

        sys.stdout.write("MusicBrainz lookup URL %s\n" %
            self.ittoc.getMusicBrainzSubmitURL())

        self.program.metadata = self.program.getMusicBrainz(self.ittoc,
            self.mbdiscid,
            release=self.options.release_id,
            country=self.options.country,
            prompt=self.options.prompt)

        if not self.program.metadata:
            # fall back to FreeDB for lookup
            cddbid = self.ittoc.getCDDBValues()
            cddbmd = self.program.getCDDB(cddbid)
            if cddbmd:
                sys.stdout.write('FreeDB identifies disc as %s\n' % cddbmd)

            # also used by rip cd info
            if not getattr(self.options, 'unknown', False):
                logger.critical("unable to retrieve disc metadata, "
                                "--unknown not passed")
                return -1

        # FIXME ?????
        # Hackish fix for broken commit
        offset = 0
        info = drive.getDeviceInfo(self.device)
        if info:
            try:
                offset = self.config.getReadOffset(*info)
            except KeyError:
                pass

        # now, read the complete index table, which is slower
        self.itable = self.program.getTable(self.runner,
            self.ittoc.getCDDBDiscId(),
            self.ittoc.getMusicBrainzDiscId(), self.device, offset)

        assert self.itable.getCDDBDiscId() == self.ittoc.getCDDBDiscId(), \
            "full table's id %s differs from toc id %s" % (
                self.itable.getCDDBDiscId(), self.ittoc.getCDDBDiscId())
        assert self.itable.getMusicBrainzDiscId() == \
            self.ittoc.getMusicBrainzDiscId(), \
            "full table's mb id %s differs from toc id mb %s" % (
            self.itable.getMusicBrainzDiscId(),
            self.ittoc.getMusicBrainzDiscId())
        assert self.itable.getAccurateRipURL() == \
            self.ittoc.getAccurateRipURL(), \
            "full table's AR URL %s differs from toc AR URL %s" % (
            self.itable.getAccurateRipURL(), self.ittoc.getAccurateRipURL())

        if self.program.metadata:
            self.program.metadata.discid = self.ittoc.getMusicBrainzDiscId()

        # result

        self.program.result.cdrdaoVersion = cdrdao.getCDRDAOVersion()
        self.program.result.cdparanoiaVersion = \
            cdparanoia.getCdParanoiaVersion()
        info = drive.getDeviceInfo(self.device)
        if info:
            try:
                self.program.result.cdparanoiaDefeatsCache = \
                    self.config.getDefeatsCache(*info)
            except KeyError, e:
                logger.debug('Got key error: %r' % (e, ))
        self.program.result.artist = self.program.metadata \
            and self.program.metadata.artist \
            or 'Unknown Artist'
        self.program.result.title = self.program.metadata \
            and self.program.metadata.title \
            or 'Unknown Title'
        try:
            import cdio
            _, self.program.result.vendor, self.program.result.model, \
                self.program.result.release = \
                cdio.Device(self.device).get_hwinfo()
        except ImportError:
            raise ImportError("Pycdio module import failed.\n"
                              "This is a hard dependency: if not "
                              "available please install it")

        self.doCommand()

        if self.options.eject in ('success', 'always'):
            utils.eject_device(self.device)

    def doCommand(self):
        pass


class Info(_CD):
    summary = "retrieve information about the currently inserted CD"
    description = ("Display musicbrainz, CDDB/FreeDB, and AccurateRip"
                   "information for the currently inserted CD.")
    eject = False

    # Requires opts.device

    def add_arguments(self):
        _CD.add_arguments(self.parser)

class Rip(_CD):
    summary = "rip CD"
    # see morituri.common.program.Program.getPath for expansion
    description = """
Rips a CD.

%s

Paths to track files referenced in .cue and .m3u files will be made
relative to the directory of the disc files.

All files will be created relative to the given output directory.
Log files will log the path to tracks relative to this directory.
""" % TEMPLATE_DESCRIPTION
    formatter_class = argparse.ArgumentDefaultsHelpFormatter

    # Requires opts.record
    # Requires opts.device

    def add_arguments(self):
        loggers = result.getLoggers().keys()
        default_offset = None
        info = drive.getDeviceInfo(self.opts.device)
        if info:
            try:
                default_offset = config.Config().getReadOffset(*info)
                sys.stdout.write("Using configured read offset %d\n" %
                                  default_offset)
            except KeyError:
                pass

        _CD.add_arguments(self.parser)

        self.parser.add_argument('-L', '--logger',
            action="store", dest="logger", default='morituri',
            help="logger to use (choose from '" + "', '".join(loggers) + "')")
        # FIXME: get from config
        self.parser.add_argument('-o', '--offset',
            action="store", dest="offset", default=default_offset,
            help="sample read offset")
        self.parser.add_argument('-x', '--force-overread',
            action="store_true", dest="overread", default=False,
            help="Force overreading into the lead-out portion of the disc. "
                "Works only if the patched cdparanoia package is installed "
                "and the drive supports this feature. ")
        self.parser.add_argument('-O', '--output-directory',
            action="store", dest="output_directory",
            default=os.path.relpath(os.getcwd()),
            help="output directory; will be included in file paths in log")
        self.parser.add_argument('-W', '--working-directory',
            action="store", dest="working_directory",
            help="working directory; morituri will change to this directory "
                "and files will be created relative to it when not absolute")
        self.parser.add_argument('--track-template',
            action="store", dest="track_template",
            default=DEFAULT_TRACK_TEMPLATE,
            help="template for track file naming (default default)")
        self.parser.add_argument('--disc-template',
            action="store", dest="disc_template",
            default=DEFAULT_DISC_TEMPLATE,
            help="template for disc file naming (default default)")
        self.parser.add_argument('-U', '--unknown',
            action="store_true", dest="unknown",
            help="whether to continue ripping if the CD is unknown",
            default=False)

    def handle_arguments(self):
        self.options.output_directory = os.path.expanduser(self.options.output_directory)

        self.options.track_template = self.options.track_template.decode('utf-8')
        self.options.disc_template = self.options.disc_template.decode('utf-8')

        if self.options.offset is None:
            raise ValueError("Drive offset is unconfigured.\n"
                             "Please install pycdio and run 'whipper offset "
                             "find' to detect your drive's offset or set it "
                             "manually in the configuration file. It can "
                             "also be specified at runtime using the "
                             "'--offset=value' argument")


        if self.options.working_directory is not None:
            self.options.working_directory = os.path.expanduser(self.options.working_directory)

        if self.options.logger:
            try:
                self.logger = result.getLoggers()[self.options.logger]()
            except KeyError:
                msg = "No logger named %s found!" % self.options.logger
                logger.critical(msg)
                raise ValueError(msg)


    def doCommand(self):
        self.program.setWorkingDirectory(self.options.working_directory)
        self.program.outdir = self.options.output_directory.decode('utf-8')
        self.program.result.offset = int(self.options.offset)
        self.program.result.overread = self.options.overread
        self.program.result.logger = self.options.logger

        ### write disc files
        disambiguate = False
        while True:
            discName = self.program.getPath(self.program.outdir,
                self.options.disc_template, self.mbdiscid, 0,
                disambiguate=disambiguate)
            dirname = os.path.dirname(discName)
            if os.path.exists(dirname):
                sys.stdout.write("Output directory %s already exists\n" %
                    dirname.encode('utf-8'))
                logs = glob.glob(os.path.join(dirname, '*.log'))
                if logs:
                    sys.stdout.write(
                        "Output directory %s is a finished rip\n" %
                        dirname.encode('utf-8'))
                    if not disambiguate:
                        disambiguate = True
                        continue
                    return
                else:
                    break

            else:
                sys.stdout.write("Creating output directory %s\n" %
                    dirname.encode('utf-8'))
                os.makedirs(dirname)
                break

        # FIXME: say when we're continuing a rip
        # FIXME: disambiguate if the pre-existing rip is different


        # FIXME: turn this into a method

        def ripIfNotRipped(number):
            logger.debug('ripIfNotRipped for track %d' % number)
            # we can have a previous result
            trackResult = self.program.result.getTrackResult(number)
            if not trackResult:
                trackResult = result.TrackResult()
                self.program.result.tracks.append(trackResult)
            else:
                logger.debug('ripIfNotRipped have trackresult, path %r' %
                    trackResult.filename)

            path = self.program.getPath(self.program.outdir,
                self.options.track_template,
                self.mbdiscid, number,
                disambiguate=disambiguate) \
                + '.' + 'flac'
            logger.debug('ripIfNotRipped: path %r' % path)
            trackResult.number = number

            assert type(path) is unicode, "%r is not unicode" % path
            trackResult.filename = path
            if number > 0:
                trackResult.pregap = self.itable.tracks[number - 1].getPregap()

                trackResult.pre_emphasis = self.itable.tracks[number - 1].pre_emphasis

            # FIXME: optionally allow overriding reripping
            if os.path.exists(path):
                if path != trackResult.filename:
                    # the path is different (different name/template ?)
                    # but we can copy it
                    logger.debug('previous result %r, expected %r' % (
                        trackResult.filename, path))

                sys.stdout.write('Verifying track %d of %d: %s\n' % (
                    number, len(self.itable.tracks),
                    os.path.basename(path).encode('utf-8')))
                if not self.program.verifyTrack(self.runner, trackResult):
                    sys.stdout.write('Verification failed, reripping...\n')
                    os.unlink(path)

            if not os.path.exists(path):
                logger.debug('path %r does not exist, ripping...' % path)
                tries = 0
                # we reset durations for test and copy here
                trackResult.testduration = 0.0
                trackResult.copyduration = 0.0
                extra = ""
                while tries < MAX_TRIES:
                    tries += 1
                    if tries > 1:
                        extra = " (try %d)" % tries
                    sys.stdout.write('Ripping track %d of %d%s: %s\n' % (
                        number, len(self.itable.tracks), extra,
                        os.path.basename(path).encode('utf-8')))
                    try:
                        logger.debug('ripIfNotRipped: track %d, try %d',
                            number, tries)
                        self.program.ripTrack(self.runner, trackResult,
                            offset=int(self.options.offset),
                            device=self.device,
                            taglist=self.program.getTagList(number),
                            overread=self.options.overread,
                            what='track %d of %d%s' % (
                                number, len(self.itable.tracks), extra))
                        break
                    except Exception, e:
                        logger.debug('Got exception %r on try %d',
                            e, tries)


                if tries == MAX_TRIES:
                    logger.critical('Giving up on track %d after %d times' % (
                        number, tries))
                    raise RuntimeError(
                        "track can't be ripped. "
                        "Rip attempts number is equal to 'MAX_TRIES'")
                if trackResult.testcrc == trackResult.copycrc:
                    sys.stdout.write('Checksums match for track %d\n' %
                        number)
                else:
                    sys.stdout.write(
                        'ERROR: checksums did not match for track %d\n' %
                        number)
                    raise

                sys.stdout.write('Peak level: {:.2%} \n'.format(trackResult.peak))

                sys.stdout.write('Rip quality: {:.2%}\n'.format(trackResult.quality))

            # overlay this rip onto the Table
            if number == 0:
                # HTOA goes on index 0 of track 1
                # ignore silence in PREGAP
                if trackResult.peak <= SILENT:
                    logger.debug('HTOA peak %r is below SILENT threshold, disregarding', trackResult.peak)
                    self.itable.setFile(1, 0, None,
                        self.ittoc.getTrackStart(1), number)
                    logger.debug('Unlinking %r', trackResult.filename)
                    os.unlink(trackResult.filename)
                    trackResult.filename = None
                    sys.stdout.write('HTOA discarded, contains digital silence\n')
                else:
                    self.itable.setFile(1, 0, trackResult.filename,
                        self.ittoc.getTrackStart(1), number)
            else:
                self.itable.setFile(number, 1, trackResult.filename,
                    self.ittoc.getTrackLength(number), number)

            self.program.saveRipResult()


        # check for hidden track one audio
        htoapath = None
        htoa = self.program.getHTOA()
        if htoa:
            start, stop = htoa
            sys.stdout.write(
                'Found Hidden Track One Audio from frame %d to %d\n' % (
                start, stop))

            # rip it
            ripIfNotRipped(0)
            htoapath = self.program.result.tracks[0].filename

        for i, track in enumerate(self.itable.tracks):
            # FIXME: rip data tracks differently
            if not track.audio:
                sys.stdout.write(
                    'WARNING: skipping data track %d, not implemented\n' % (
                    i + 1, ))
                # FIXME: make it work for now
                track.indexes[1].relative = 0
                continue

            ripIfNotRipped(i + 1)

        ### write disc files
        discName = self.program.getPath(self.program.outdir,
            self.options.disc_template, self.mbdiscid, 0,
            disambiguate=disambiguate)
        dirname = os.path.dirname(discName)
        if not os.path.exists(dirname):
            os.makedirs(dirname)

        logger.debug('writing cue file for %r', discName)
        self.program.writeCue(discName)

        # write .m3u file
        logger.debug('writing m3u file for %r', discName)
        m3uPath = u'%s.m3u' % discName
        handle = open(m3uPath, 'w')
        u = u'#EXTM3U\n'
        handle.write(u.encode('utf-8'))

        def writeFile(handle, path, length):
            targetPath = common.getRelativePath(path, m3uPath)
            u = u'#EXTINF:%d,%s\n' % (length, targetPath)
            handle.write(u.encode('utf-8'))
            u = '%s\n' % targetPath
            handle.write(u.encode('utf-8'))


        if htoapath:
            writeFile(handle, htoapath,
                self.itable.getTrackStart(1) / common.FRAMES_PER_SECOND)

        for i, track in enumerate(self.itable.tracks):
            if not track.audio:
                continue

            path = self.program.getPath(self.program.outdir,
                self.options.track_template, self.mbdiscid, i + 1,
                disambiguate=disambiguate) + '.' + 'flac'
            writeFile(handle, path,
                self.itable.getTrackLength(i + 1) / common.FRAMES_PER_SECOND)

        handle.close()

        # verify using accuraterip
        url = self.ittoc.getAccurateRipURL()
        sys.stdout.write("AccurateRip URL %s\n" % url)

        accucache = accurip.AccuCache()
        try:
            responses = accucache.retrieve(url)
        except urllib2.URLError, e:
            if isinstance(e.args[0], socket.gaierror):
                if e.args[0].errno == -2:
                    sys.stdout.write("Warning: network error: %r\n" % (
                        e.args[0], ))
                    responses = None
                else:
                    raise
            else:
                raise

        if not responses:
            sys.stdout.write('Album not found in AccurateRip database\n')

        if responses:
            sys.stdout.write('%d AccurateRip reponses found\n' %
                len(responses))

            if responses[0].cddbDiscId != self.itable.getCDDBDiscId():
                sys.stdout.write(
                    "AccurateRip response discid different: %s\n" %
                    responses[0].cddbDiscId)


        self.program.verifyImage(self.runner, responses)

        sys.stdout.write("\n".join(
            self.program.getAccurateRipResults()) + "\n")

        self.program.saveRipResult()

        # write log file
        self.program.writeLog(discName, self.logger)


class CD(BaseCommand):
    summary = "handle CDs"
    description = "Display and rip CD-DA and metadata."
    device_option = True

    subcommands = {
        'info': Info,
        'rip': Rip
    }
