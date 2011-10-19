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

from morituri.extern.task import task, gstreamer

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
        encodetask = encode.EncodeTask(fromPath, toPath, profile)

        runner.run(encodetask)

class MusicBrainz(logcommand.LogCommand):

    summary = "examine MusicBrainz info"


    def do(self, args):
        try:
            discId = unicode(args[0])
        except IndexError:
            self.stdout.write('Please specify a MusicBrainz disc id.\n')
            return 3

        from morituri.common import musicbrainz
        metadatas = musicbrainz.musicbrainz(discId)

        self.stdout.write('%d releases\n' % len(metadatas))
        for i, md in enumerate(metadatas):
            self.stdout.write('- Release %d:\n' % (i + 1, ))
            self.stdout.write('    Artist: %r\n' % md.artist)
            self.stdout.write('    Title:  %r\n' % md.title)
            self.stdout.write('    URL: %r\n' % md.url)
            self.stdout.write('    Tracks: %r\n' % len(md.tracks))
            for j, track in enumerate(md.tracks):
                self.stdout.write('      Track %2d: %r - %r\n' % (
                    j + 1, track.artist, track.title))

class Debug(logcommand.LogCommand):
    summary = "debug internals"

    subCommandClasses = [Checksum, Encode, MusicBrainz, ]
