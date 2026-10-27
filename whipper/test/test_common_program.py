# -*- Mode: Python; test-case-name: whipper.test.test_common_program -*-
# vi:si:et:sw=4:sts=4:ts=4


import os
import shutil
import unittest

from tempfile import NamedTemporaryFile, TemporaryDirectory
from whipper.common import program, mbngs, config
from whipper.command.cd import DEFAULT_DISC_TEMPLATE
from whipper.result.logger import WhipperLogger
from whipper.result.result import RipResult, TrackResult
from whipper.common.yaml import YAML
from whipper.test.test_result_logger import MockImageTable


class PathTestCase(unittest.TestCase):

    def testStandardTemplateEmpty(self):
        prog = program.Program(config.Config())

        path = prog.getPath('/tmp', DEFAULT_DISC_TEMPLATE,
                            'mbdiscid', None)
        self.assertEqual(path, ('/tmp/unknown/Unknown Artist - mbdiscid/'
                                'Unknown Artist - mbdiscid'))

    def testStandardTemplateFilled(self):
        prog = program.Program(config.Config())
        md = mbngs.DiscMetadata()
        md.artist = md.sortName = 'Jeff Buckley'
        md.releaseTitle = 'Grace'

        path = prog.getPath('/tmp', DEFAULT_DISC_TEMPLATE,
                            'mbdiscid', md, 0)
        self.assertEqual(path, ('/tmp/unknown/Jeff Buckley - Grace/'
                                'Jeff Buckley - Grace'))

    def testIssue66TemplateFilled(self):
        prog = program.Program(config.Config())
        md = mbngs.DiscMetadata()
        md.artist = md.sortName = 'Jeff Buckley'
        md.releaseTitle = 'Grace'

        path = prog.getPath('/tmp', '%A/%d', 'mbdiscid', md, 0)
        self.assertEqual(path,
                         '/tmp/Jeff Buckley/Grace')


class WriteLogTestCase(unittest.TestCase):
    def testPrivatePathsOnlyChangeInWrittenLog(self):
        with TemporaryDirectory() as directory:
            album = os.path.join(directory, 'private-user', 'Album')
            os.makedirs(os.path.join(album, 'Disc 1'))
            prog = program.Program(config.Config())
            prog.result = RipResult()
            prog.result.table = MockImageTable()
            names = ('00. Hidden.flac', 'Disc 1/01.flac')
            for number, relative in enumerate(names):
                track = TrackResult()
                track.number = number
                track.filename = os.path.join(album, relative)
                with open(track.filename, 'wb') as handle:
                    handle.write(b'synthetic audio placeholder')
                prog.result.tracks.append(track)
            original = [t.filename for t in prog.result.tracks]
            for disc in ('disc', 'disc.partial'):
                with self.subTest(disc=disc):
                    filename = prog.writeLog(os.path.join(album, disc),
                                             WhipperLogger())
                    self.assertEqual(prog.logPath, filename)
                    with open(filename) as handle:
                        parsed = YAML(typ='rt', pure=True).load(handle.read())
                    self.assertEqual(parsed['Tracks'][0]['Filename'],
                                     '00. Hidden.flac')
                    self.assertEqual(parsed['Tracks'][1]['Filename'],
                                     'Disc 1/01.flac')
                    self.assertEqual([t.filename for t in prog.result.tracks],
                                     original)
                    for path in original:
                        with open(path, 'rb') as handle:
                            self.assertEqual(handle.read(),
                                             b'synthetic audio placeholder')

    def testLoggerPluginSignatureIsUnchanged(self):
        class PluginLogger(WhipperLogger):
            def log(self, ripResult):
                return 'plugin log\n'

        with TemporaryDirectory() as directory:
            prog = program.Program(config.Config())
            prog.result = RipResult()
            filename = prog.writeLog(os.path.join(directory, 'disc'),
                                     PluginLogger())
            with open(filename) as handle:
                self.assertEqual(handle.read(), 'plugin log\n')


# TODO: Test cover art embedding too.
class CoverArtTestCase(unittest.TestCase):

    @staticmethod
    def _mock_get_front_image(release_id):
        """
        Mock `musicbrainzngs.get_front_image` function.

        Reads a local cover art image and returns its binary data.

        :param release_id: a release id (self.program.metadata.mbid)
        :type  release_id: str
        :returns: the binary content of the local cover art image
        :rtype: bytes
        """
        filename = '%s.jpg' % release_id
        path = os.path.join(os.path.dirname(__file__), filename)
        with open(path, 'rb') as f:
            return f.read()

    def _mock_getCoverArt(self, path, release_id):
        """
        Mock `common.program.getCoverArt` function.

        :param path: where to store the fetched image
        :type  path: str
        :param release_id: a release id (self.program.metadata.mbid)
        :type  release_id: str
        :returns: path to the downloaded cover art
        :rtype: str
        """
        cover_art_path = os.path.join(path, 'cover.jpg')

        data = self._mock_get_front_image(release_id)

        with NamedTemporaryFile(suffix='.cover.jpg', delete=False) as f:
            f.write(data)
        os.chmod(f.name, 0o644)
        shutil.move(f.name, cover_art_path)
        return cover_art_path

    def testCoverArtPath(self):
        """Test whether a fetched cover art is saved properly."""
        # Using: Dummy by Portishead
        # https://musicbrainz.org/release/76df3287-6cda-33eb-8e9a-044b5e15ffdd
        path = os.path.dirname(__file__)
        release_id = "76df3287-6cda-33eb-8e9a-044b5e15ffdd"
        coverArtPath = self._mock_getCoverArt(path, release_id)
        self.assertTrue(os.path.isfile(coverArtPath))
