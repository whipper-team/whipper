# -*- Mode: Python -*-
# vi:si:et:sw=4:sts=4:ts=4

# Copyright (C) 2009 Thomas Vander Stichele

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

import argparse
import sys

from whipper.command.basecommand import BaseCommand
from whipper.common import cache, task
from whipper.result import result

import logging
logger = logging.getLogger(__name__)


class RCCue(BaseCommand):
    summary = "write a cue file for the cached result"
    description = summary

    def do(self, args):
        self._cache = cache.ResultCache()

        try:
            discid = args[0]
        except IndexError:
            sys.stderr.write(
                'Please specify a cddb disc id\n')
            return 3

        persisted = self._cache.getRipResult(discid, create=False)

        if not persisted:
            sys.stderr.write(
                'Could not find a result for cddb disc id %s\n' % discid)
            return 3

        sys.stdout.write(persisted.object.table.cue().encode('utf-8'))


class RCList(BaseCommand):
    summary = "list cached results"
    description = summary

    def do(self, args):
        self._cache = cache.ResultCache()
        results = []

        for i in self._cache.getIds():
            r = self._cache.getRipResult(i, create=False)
            results.append((r.object.artist, r.object.title, i))

        results.sort()

        for artist, title, cddbid in results:
            if artist is None:
                artist = '(None)'
            if title is None:
                title = '(None)'

            sys.stdout.write('%s: %s - %s\n' % (
                cddbid, artist.encode('utf-8'), title.encode('utf-8')))


class RCLog(BaseCommand):
    summary = "write a log file for the cached result"
    description = summary
    formatter_class = argparse.ArgumentDefaultsHelpFormatter

    def add_arguments(self):
        loggers = result.getLoggers().keys()

        self.parser.add_argument(
            '-L', '--logger',
            action="store", dest="logger",
            default='whipper',
            help="logger to use (choose from '" + "', '".join(loggers) + "')"
        )

    def do(self, args):
        self._cache = cache.ResultCache()

        persisted = self._cache.getRipResult(args[0], create=False)

        if not persisted:
            sys.stderr.write(
                'Could not find a result for cddb disc id %s\n' % args[0])
            return 3

        try:
            klazz = result.getLoggers()[self.options.logger]
        except KeyError:
            sys.stderr.write("No logger named %s found!\n" % (
                self.options.logger))
            return 3

        logger = klazz()
        sys.stdout.write(logger.log(persisted.object).encode('utf-8'))


class ResultCache(BaseCommand):
    summary = "debug result cache"
    description = summary

    subcommands = {
        'cue': RCCue,
        'list': RCList,
        'log': RCLog,
    }


class Checksum(BaseCommand):
    summary = "run a checksum task"
    description = summary

    def add_arguments(self):
        self.parser.add_argument('files', nargs='+', action='store',
                                 help="audio files to checksum")

    def do(self):
        runner = task.SyncRunner()
        # here to avoid import gst eating our options
        from whipper.common import checksum

        for f in self.options.files:
            fromPath = unicode(f)
            checksumtask = checksum.CRC32Task(fromPath)
            runner.run(checksumtask)
            sys.stdout.write('Checksum: %08x\n' % checksumtask.checksum)


class Encode(BaseCommand):
    summary = "run an encode task"
    description = summary

    def add_arguments(self):
        self.parser.add_argument('input', action='store',
                                 help="audio file to encode")
        self.parser.add_argument('output', nargs='?', action='store',
                                 help="output path")

    def do(self):
        from whipper.common import encode

        try:
            fromPath = unicode(self.options.input)
        except IndexError:
            # unexercised after BaseCommand
            sys.stdout.write('Please specify an input file.\n')
            return 3

        try:
            toPath = unicode(self.options.output)
        except IndexError:
            toPath = fromPath + '.flac'

        runner = task.SyncRunner()

        logger.debug('Encoding %s to %s',
                     fromPath.encode('utf-8'),
                     toPath.encode('utf-8'))
        encodetask = encode.FlacEncodeTask(fromPath, toPath)

        runner.run(encodetask)

        # I think we want this to be
        # fromPath, not toPath, since the sox peak task, afaik, works on wave
        # files
        peaktask = encode.SoxPeakTask(fromPath)
        runner.run(peaktask)

        sys.stdout.write('Peak level: %r\n' % peaktask.peak)
        sys.stdout.write('Encoded to %s\n' % toPath.encode('utf-8'))


class Tag(BaseCommand):
    summary = "run a tag reading task"
    description = summary

    def add_arguments(self):
        self.parser.add_argument('file', action='store',
                                 help="audio file to tag")

    def do(self):
        try:
            path = unicode(self.options.file)
        except IndexError:
            sys.stdout.write('Please specify an input file.\n')
            return 3

        runner = task.SyncRunner()

        from whipper.common import encode
        logger.debug('Reading tags from %s' % path.encode('utf-8'))
        tagtask = encode.TagReadTask(path)

        runner.run(tagtask)

        for key in tagtask.taglist.keys():
            sys.stdout.write('%s: %r\n' % (key, tagtask.taglist[key]))


class MusicBrainzNGS(BaseCommand):
    summary = "examine MusicBrainz NGS info"
    description = """Look up a MusicBrainz disc id and output information.

You can get the MusicBrainz disc id with whipper cd info.

Example disc id: KnpGsLhvH.lPrNc1PBL21lb9Bg4-"""

    def add_arguments(self):
        self.parser.add_argument('mbdiscid', action='store',
                                 help="MB disc id to look up")

    def do(self):
        try:
            discId = unicode(self.options.mbdiscid)
        except IndexError:
            sys.stdout.write('Please specify a MusicBrainz disc id.\n')
            return 3

        from whipper.common import mbngs
        metadatas = mbngs.musicbrainz(discId, record=self.options.record)

        sys.stdout.write('%d releases\n' % len(metadatas))
        for i, md in enumerate(metadatas):
            sys.stdout.write('- Release %d:\n' % (i + 1, ))
            sys.stdout.write('    Artist: %s\n' % md.artist.encode('utf-8'))
            sys.stdout.write('    Title:  %s\n' % md.title.encode('utf-8'))
            sys.stdout.write('    Type:   %s\n' % md.releaseType.encode('utf-8'))  # noqa: E501
            sys.stdout.write('    URL: %s\n' % md.url)
            sys.stdout.write('    Tracks: %d\n' % len(md.tracks))
            if md.catalogNumber:
                sys.stdout.write('    Cat no: %s\n' % md.catalogNumber)
            if md.barcode:
                sys.stdout.write('   Barcode: %s\n' % md.barcode)

            for j, track in enumerate(md.tracks):
                sys.stdout.write('      Track %2d: %s - %s\n' % (
                    j + 1, track.artist.encode('utf-8'),
                    track.title.encode('utf-8')))


class CDParanoia(BaseCommand):
    summary = "show cdparanoia version"
    description = summary

    def do(self):
        from whipper.program import cdparanoia
        version = cdparanoia.getCdParanoiaVersion()
        sys.stdout.write("cdparanoia version: %s\n" % version)


class CDRDAO(BaseCommand):
    summary = "show cdrdao version"
    description = summary

    def do(self):
        from whipper.program import cdrdao
        version = cdrdao.getCDRDAOVersion()
        sys.stdout.write("cdrdao version: %s\n" % version)


class Version(BaseCommand):
    summary = "debug version getting"
    description = summary

    subcommands = {
        'cdparanoia': CDParanoia,
        'cdrdao': CDRDAO,
    }


class Debug(BaseCommand):
    summary = "debug internals"
    description = "debug internals"

    subcommands = {
        'checksum': Checksum,
        'encode': Encode,
        'tag': Tag,
        'musicbrainzngs': MusicBrainzNGS,
        'resultcache': ResultCache,
        'version': Version,
    }
