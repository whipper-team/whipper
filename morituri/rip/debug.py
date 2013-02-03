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

from morituri.common import logcommand
from morituri.result import result

from morituri.common import task, cache


class RCList(logcommand.LogCommand):

    name = "list"
    summary = "list cached results"

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

            self.stdout.write('%s: %s - %s\n' % (
                cddbid, artist.encode('utf-8'), title.encode('utf-8')))
        

class RCLog(logcommand.LogCommand):

    name = "log"
    summary = "write a log file for the cached result"

    def addOptions(self):
        loggers = result.getLoggers().keys()

        self.parser.add_option('-L', '--logger',
            action="store", dest="logger",
            default='morituri',
            help="logger to use "
                "(default '%default', choose from '" +
                    "', '".join(loggers) + "')")

    def do(self, args):
        self._cache = cache.ResultCache()

        persisted = self._cache.getRipResult(args[0], create=False)

        if not persisted:
            self.stderr.write(
                'Could not find a result for cddb disc id %s\n' % args[0])
            return 3

        try:
            klazz = result.getLoggers()[self.options.logger]
        except KeyError:
            self.stderr.write("No logger named %s found!\n" % (
                self.options.logger))
            return 3

        logger = klazz()
        self.stdout.write(logger.log(persisted.object).encode('utf-8'))
 

class ResultCache(logcommand.LogCommand):

    summary = "debug result cache"
    aliases = ['rc', ]

    subCommandClasses = [RCList, RCLog, ]


class Checksum(logcommand.LogCommand):

    summary = "run a checksum task"

    def do(self, args):
        try:
            fromPath = unicode(args[0])
        except IndexError:
            self.stdout.write('Please specify an input file.\n')
            return 3

        runner = task.SyncRunner()

        # here to avoid import gst eating our options
        from morituri.common import checksum
        checksumtask = checksum.CRC32Task(fromPath)

        runner.run(checksumtask)

        self.stdout.write('Checksum: %08x\n' % checksumtask.checksum)


class Encode(logcommand.LogCommand):

    summary = "run an encode task"

    def addOptions(self):
        # here to avoid import gst eating our options
        from morituri.common import encode

        default = 'flac'
        self.parser.add_option('', '--profile',
            action="store", dest="profile",
            help="profile for encoding (default '%s', choices '%s')" % (
                default, "', '".join(encode.PROFILES.keys())),
            default=default)

    def do(self, args):
        try:
            fromPath = unicode(args[0])
        except IndexError:
            self.stdout.write('Please specify an input file.\n')
            return 3

        try:
            toPath = unicode(args[1])
        except IndexError:
            toPath = fromPath + '.' + self.options.profile

        runner = task.SyncRunner()

        from morituri.common import encode
        profile = encode.PROFILES[self.options.profile]()
        self.debug('Encoding %s to %s',
            fromPath.encode('utf-8'),
            toPath.encode('utf-8'))
        encodetask = encode.EncodeTask(fromPath, toPath, profile)

        runner.run(encodetask)

class Tag(logcommand.LogCommand):

    summary = "run a tag reading task"

    def do(self, args):
        try:
            path = unicode(args[0])
        except IndexError:
            self.stdout.write('Please specify an input file.\n')
            return 3

        runner = task.SyncRunner()

        from morituri.common import encode
        self.debug('Reading tags from %s' % path.encode('utf-8'))
        tagtask = encode.TagReadTask(path)

        runner.run(tagtask)

        for key in tagtask.taglist.keys():
            self.stdout.write('%s: %r\n' % (key, tagtask.taglist[key]))


class MusicBrainzNGS(logcommand.LogCommand):

    usage = "[MusicBrainz disc id]"
    summary = "examine MusicBrainz NGS info"
    description = """Look up a MusicBrainz disc id and output information.

Example disc id: KnpGsLhvH.lPrNc1PBL21lb9Bg4-"""

    def do(self, args):
        try:
            discId = unicode(args[0])
        except IndexError:
            self.stdout.write('Please specify a MusicBrainz disc id.\n')
            return 3

        from morituri.common import musicbrainzngs
        metadatas = musicbrainzngs.musicbrainz(discId)

        self.stdout.write('%d releases\n' % len(metadatas))
        for i, md in enumerate(metadatas):
            self.stdout.write('- Release %d:\n' % (i + 1, ))
            self.stdout.write('    Artist: %s\n' % md.artist.encode('utf-8'))
            self.stdout.write('    Title:  %s\n' % md.title.encode('utf-8'))
            self.stdout.write('    Type:   %s\n' % md.releaseType.encode('utf-8'))
            self.stdout.write('    URL: %s\n' % md.url)
            self.stdout.write('    Tracks: %d\n' % len(md.tracks))
            if md.catalogNumber:
                self.stdout.write('    Cat no: %s\n' % md.catalogNumber)
            if md.barcode:
                self.stdout.write('   Barcode: %s\n' % md.barcode)

            for j, track in enumerate(md.tracks):
                self.stdout.write('      Track %2d: %s - %s\n' % (
                    j + 1, track.artist.encode('utf-8'),
                    track.title.encode('utf-8')))


class Debug(logcommand.LogCommand):

    summary = "debug internals"

    subCommandClasses = [Checksum, Encode, Tag, MusicBrainzNGS, ResultCache]
