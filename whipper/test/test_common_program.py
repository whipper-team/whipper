# -*- Mode: Python; test-case-name: whipper.test.test_common_program -*-
# vi:si:et:sw=4:sts=4:ts=4


import os
import shutil
import unittest

from tempfile import NamedTemporaryFile
from whipper.common import program, mbngs, config
from whipper.command.cd import DEFAULT_DISC_TEMPLATE


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
        md.title = 'Grace'

        path = prog.getPath('/tmp', DEFAULT_DISC_TEMPLATE,
                            'mbdiscid', md, 0)
        self.assertEqual(path, ('/tmp/unknown/Jeff Buckley - Grace/'
                                'Jeff Buckley - Grace'))

    def testIssue66TemplateFilled(self):
        prog = program.Program(config.Config())
        md = mbngs.DiscMetadata()
        md.artist = md.sortName = 'Jeff Buckley'
        md.title = 'Grace'

        path = prog.getPath('/tmp', '%A/%d', 'mbdiscid', md, 0)
        self.assertEqual(path,
                         '/tmp/Jeff Buckley/Grace')


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
