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
import math
import glob
import urllib2
import socket

import gobject
gobject.threads_init()

from morituri.common import logcommand, common, accurip, gstreamer
from morituri.common import drive, program, task
from morituri.result import result
from morituri.program import cdrdao, cdparanoia
from morituri.rip import common as rcommon

from morituri.extern.command import command


MAX_TRIES = 5


class _CD(logcommand.LogCommand):

    """
    @type program: L{program.Program}
    @ivar eject:   whether to eject the drive after completing
    """

    eject = True

    def addOptions(self):
        # FIXME: have a cache of these pickles somewhere
        self.parser.add_option('-T', '--toc-pickle',
            action="store", dest="toc_pickle",
            help="pickle to use for reading and writing the TOC")
        self.parser.add_option('-R', '--release-id',
            action="store", dest="release_id",
            help="MusicBrainz release id to match to (if there are multiple)")


    def do(self, args):
        self.program = program.Program(self.getRootCommand().config,
            record=self.getRootCommand().record,
            stdout=self.stdout)
        self.runner = task.SyncRunner()

        # if the device is mounted (data session), unmount it
        self.device = self.parentCommand.options.device
        self.stdout.write('Checking device %s\n' % self.device)

        self.program.loadDevice(self.device)
        self.program.unmountDevice(self.device)

        # first, read the normal TOC, which is fast
        self.ittoc = self.program.getFastToc(self.runner,
            self.options.toc_pickle,
            self.device)

        # already show us some info based on this
        self.program.getRipResult(self.ittoc.getCDDBDiscId())
        self.stdout.write("CDDB disc id: %s\n" % self.ittoc.getCDDBDiscId())
        self.mbdiscid = self.ittoc.getMusicBrainzDiscId()
        self.stdout.write("MusicBrainz disc id %s\n" % self.mbdiscid)

        self.stdout.write("MusicBrainz lookup URL %s\n" %
            self.ittoc.getMusicBrainzSubmitURL())

        self.program.metadata = self.program.getMusicBrainz(self.ittoc,
            self.mbdiscid,
            release=self.options.release_id)

        if not self.program.metadata:
            # fall back to FreeDB for lookup
            cddbid = self.ittoc.getCDDBValues()
            cddbmd = self.program.getCDDB(cddbid)
            if cddbmd:
                self.stdout.write('FreeDB identifies disc as %s\n' % cddbmd)

            # also used by rip cd info
            if not getattr(self.options, 'unknown', False):
                if self.eject:
                    self.program.ejectDevice(self.device)
                return -1

        # now, read the complete index table, which is slower

        self.itable = self.program.getTable(self.runner,
            self.ittoc.getCDDBDiscId(),
            self.ittoc.getMusicBrainzDiscId(), self.device)

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
        info = drive.getDeviceInfo(self.parentCommand.options.device)
        if info:
            try:
                self.program.result.cdparanoiaDefeatsCache = \
                    self.getRootCommand().config.getDefeatsCache(*info)
            except KeyError, e:
                self.debug('Got key error: %r' % (e, ))
        self.program.result.artist = self.program.metadata \
            and self.program.metadata.artist \
            or 'Unknown Artist'
        self.program.result.title = self.program.metadata \
            and self.program.metadata.title \
            or 'Unknown Title'
        # cdio is optional for now
        try:
            import cdio
            _, self.program.result.vendor, self.program.result.model, \
                self.program.result.release = \
                cdio.Device(self.device).get_hwinfo()
        except ImportError:
            self.stdout.write(
                'WARNING: pycdio not installed, cannot identify drive\n')
            self.program.result.vendor = 'Unknown'
            self.program.result.model = 'Unknown'
            self.program.result.release = 'Unknown'

        self.doCommand()

        if self.eject:
            self.program.ejectDevice(self.device)

    def doCommand(self):
        pass


class Info(_CD):
    summary = "retrieve information about the currently inserted CD"

    eject = False


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
""" % rcommon.TEMPLATE_DESCRIPTION

    def addOptions(self):
        _CD.addOptions(self)

        loggers = result.getLoggers().keys()

        self.parser.add_option('-L', '--logger',
            action="store", dest="logger",
            default='morituri',
            help="logger to use "
                "(default '%default', choose from '" +
                    "', '".join(loggers) + "')")
        # FIXME: get from config
        self.parser.add_option('-o', '--offset',
            action="store", dest="offset",
            help="sample read offset (defaults to configured value, or 0)")
        self.parser.add_option('-O', '--output-directory',
            action="store", dest="output_directory",
            help="output directory; will be included in file paths in result "
                "files "
                "(defaults to absolute path to current directory; set to "
                "empty if you want paths to be relative instead) ")
        self.parser.add_option('-W', '--working-directory',
            action="store", dest="working_directory",
            help="working directory; morituri will change to this directory "
                "and files will be created relative to it when not absolute ")

        rcommon.addTemplate(self)

        default = 'flac'

        # here to avoid import gst eating our options
        from morituri.common import encode

        self.parser.add_option('', '--profile',
            action="store", dest="profile",
            help="profile for encoding (default '%s', choices '%s')" % (
                default, "', '".join(encode.PROFILES.keys())),
            default=default)
        self.parser.add_option('-U', '--unknown',
            action="store_true", dest="unknown",
            help="whether to continue ripping if the CD is unknown (%default)",
            default=False)

    def handleOptions(self, options):
        options.track_template = options.track_template.decode('utf-8')
        options.disc_template = options.disc_template.decode('utf-8')

        if options.offset is None:
            info = drive.getDeviceInfo(self.parentCommand.options.device)
            if info:
                try:
                    options.offset = self.getRootCommand(
                        ).config.getReadOffset(*info)
                    self.stdout.write("Using configured read offset %d\n" %
                        options.offset)
                except KeyError:
                    pass

        if options.offset is None:
            options.offset = 0
            self.stdout.write("""WARNING: using default offset %d.
Install pycdio and run 'rip offset find' to detect your drive's offset.
""" %
                        options.offset)
        if self.options.output_directory is None:
            self.options.output_directory = os.getcwd()

        if self.options.logger:
            try:
                klazz = result.getLoggers()[self.options.logger]
            except KeyError:
                self.stderr.write("No logger named %s found!\n" % (
                    self.options.logger))
                raise command.CommandError("No logger named %s" %
                    self.options.logger)

            self.logger = klazz()

    def doCommand(self):
        # here to avoid import gst eating our options
        from morituri.common import encode
        profile = encode.PROFILES[self.options.profile]()
        self.program.result.profileName = profile.name
        self.program.result.profilePipeline = profile.pipeline
        elementFactory = profile.pipeline.split(' ')[0]
        self.program.result.gstreamerVersion = gstreamer.gstreamerVersion()
        self.program.result.gstPythonVersion = gstreamer.gstPythonVersion()
        self.program.result.encoderVersion = gstreamer.elementFactoryVersion(
            elementFactory)

        self.program.setWorkingDirectory(self.options.working_directory)
        self.program.outdir = self.options.output_directory.decode('utf-8')
        self.program.result.offset = int(self.options.offset)

        ### write disc files
        disambiguate = False
        while True:
            discName = self.program.getPath(self.program.outdir,
                self.options.disc_template, self.mbdiscid, 0,
                profile=profile, disambiguate=disambiguate)
            dirname = os.path.dirname(discName)
            if os.path.exists(dirname):
                self.stdout.write("Output directory %s already exists\n" %
                    dirname.encode('utf-8'))
                logs = glob.glob(os.path.join(dirname, '*.log'))
                if logs:
                    self.stdout.write(
                        "Output directory %s is a finished rip\n" %
                        dirname.encode('utf-8'))
                    if not disambiguate:
                        disambiguate = True
                        continue
                    return
                else:
                    break

            else:
                self.stdout.write("Creating output directory %s\n" %
                    dirname.encode('utf-8'))
                os.makedirs(dirname)
                break

        # FIXME: say when we're continuing a rip
        # FIXME: disambiguate if the pre-existing rip is different


        # FIXME: turn this into a method

        def ripIfNotRipped(number):
            self.debug('ripIfNotRipped for track %d' % number)
            # we can have a previous result
            trackResult = self.program.result.getTrackResult(number)
            if not trackResult:
                trackResult = result.TrackResult()
                self.program.result.tracks.append(trackResult)
            else:
                self.debug('ripIfNotRipped have trackresult, path %r' %
                    trackResult.filename)

            path = self.program.getPath(self.program.outdir,
                self.options.track_template,
                self.mbdiscid, number,
                profile=profile, disambiguate=disambiguate) \
                + '.' + profile.extension
            self.debug('ripIfNotRipped: path %r' % path)
            trackResult.number = number

            assert type(path) is unicode, "%r is not unicode" % path
            trackResult.filename = path
            if number > 0:
                trackResult.pregap = self.itable.tracks[number - 1].getPregap()

            # FIXME: optionally allow overriding reripping
            if os.path.exists(path):
                if path != trackResult.filename:
                    # the path is different (different name/template ?)
                    # but we can copy it
                    self.debug('previous result %r, expected %r' % (
                        trackResult.filename, path))

                self.stdout.write('Verifying track %d of %d: %s\n' % (
                    number, len(self.itable.tracks),
                    os.path.basename(path).encode('utf-8')))
                if not self.program.verifyTrack(self.runner, trackResult):
                    self.stdout.write('Verification failed, reripping...\n')
                    os.unlink(path)

            if not os.path.exists(path):
                self.debug('path %r does not exist, ripping...' % path)
                tries = 0
                # we reset durations for test and copy here
                trackResult.testduration = 0.0
                trackResult.copyduration = 0.0
                extra = ""
                while tries < MAX_TRIES:
                    tries += 1
                    if tries > 1:
                        extra = " (try %d)" % tries
                    self.stdout.write('Ripping track %d of %d%s: %s\n' % (
                        number, len(self.itable.tracks), extra,
                        os.path.basename(path).encode('utf-8')))
                    try:
                        self.debug('ripIfNotRipped: track %d, try %d',
                            number, tries)
                        self.program.ripTrack(self.runner, trackResult,
                            offset=int(self.options.offset),
                            device=self.parentCommand.options.device,
                            profile=profile,
                            taglist=self.program.getTagList(number),
                            what='track %d of %d%s' % (
                                number, len(self.itable.tracks), extra))
                        break
                    except Exception, e:
                        self.debug('Got exception %r on try %d',
                            e, tries)


                if tries == MAX_TRIES:
                    self.error('Giving up on track %d after %d times' % (
                        number, tries))
                if trackResult.testcrc == trackResult.copycrc:
                    self.stdout.write('Checksums match for track %d\n' %
                        number)
                else:
                    self.stdout.write(
                        'ERROR: checksums did not match for track %d\n' %
                        number)
                    raise

                self.stdout.write('Peak level: %.2f %%\n' % (
                    math.sqrt(trackResult.peak) * 100.0, ))
                self.stdout.write('Rip quality: %.2f %%\n' % (
                    trackResult.quality * 100.0, ))

            # overlay this rip onto the Table
            if number == 0:
                # HTOA goes on index 0 of track 1
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
            self.stdout.write(
                'Found Hidden Track One Audio from frame %d to %d\n' % (
                start, stop))

            # rip it
            ripIfNotRipped(0)
            htoapath = self.program.result.tracks[0].filename

        for i, track in enumerate(self.itable.tracks):
            # FIXME: rip data tracks differently
            if not track.audio:
                self.stdout.write(
                    'WARNING: skipping data track %d, not implemented\n' % (
                    i + 1, ))
                # FIXME: make it work for now
                track.indexes[1].relative = 0
                continue

            ripIfNotRipped(i + 1)

        ### write disc files
        discName = self.program.getPath(self.program.outdir,
            self.options.disc_template, self.mbdiscid, 0,
            profile=profile, disambiguate=disambiguate)
        dirname = os.path.dirname(discName)
        if not os.path.exists(dirname):
            os.makedirs(dirname)

        self.debug('writing cue file for %r', discName)
        self.program.writeCue(discName)

        # write .m3u file
        self.debug('writing m3u file for %r', discName)
        m3uPath = u'%s.m3u' % discName
        handle = open(m3uPath, 'w')
        handle.write(u'#EXTM3U\n')

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
                profile=profile,
                disambiguate=disambiguate) + '.' + profile.extension
            writeFile(handle, path,
                self.itable.getTrackLength(i + 1) / common.FRAMES_PER_SECOND)

        handle.close()

        # verify using accuraterip
        url = self.ittoc.getAccurateRipURL()
        self.stdout.write("AccurateRip URL %s\n" % url)

        accucache = accurip.AccuCache()
        try:
            responses = accucache.retrieve(url)
        except urllib2.URLError, e:
            if isinstance(e.args[0], socket.gaierror):
                if e.args[0].errno == -2:
                    self.stdout.write("Warning: network error: %r\n" % (
                        e.args[0], ))
                    responses = None
                else:
                    raise
            else:
                raise

        if not responses:
            self.stdout.write('Album not found in AccurateRip database\n')

        if responses:
            self.stdout.write('%d AccurateRip reponses found\n' %
                len(responses))

            if responses[0].cddbDiscId != self.itable.getCDDBDiscId():
                self.stdout.write(
                    "AccurateRip response discid different: %s\n" %
                    responses[0].cddbDiscId)


        self.program.verifyImage(self.runner, responses)

        self.stdout.write("\n".join(
            self.program.getAccurateRipResults()) + "\n")

        self.program.saveRipResult()

        # write log file
        self.program.writeLog(discName, self.logger)

        self.program.ejectDevice(self.device)


class CD(logcommand.LogCommand):

    summary = "handle CD's"

    subCommandClasses = [Info, Rip, ]

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
