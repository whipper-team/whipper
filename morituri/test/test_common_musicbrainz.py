# -*- Mode: Python; test-case-name: morituri.test.test_common_musicbrainz -*-
# vi:si:et:sw=4:sts=4:ts=4

import os

import unittest

from morituri.common import musicbrainz


class MetadataLengthTestCase(unittest.TestCase):

    def testLamprey(self):
        from musicbrainz2 import wsxml

        path = os.path.join(os.path.dirname(__file__),
            'release.c7d919f4-3ea0-4c4b-a230-b3605f069440.xml')
        handle = open(path, "rb")

        reader = wsxml.MbXmlParser()
        wsMetadata = reader.parse(handle)
        release = wsMetadata.getRelease()
        metadata = musicbrainz._getMetadata(release)

        self.assertEquals(metadata.duration, 2962889)

    def testLadyhawke(self):
        from musicbrainz2 import wsxml

        path = os.path.join(os.path.dirname(__file__),
            'release.93a6268c-ddf1-4898-bf93-fb862b1c5c5e.xml')
        handle = open(path, "rb")

        reader = wsxml.MbXmlParser()
        wsMetadata = reader.parse(handle)
        release = wsMetadata.getRelease()
        metadata = musicbrainz._getMetadata(release)
        self.failUnless(metadata)

        # self.assertEquals(metadata.duration, 2609413)

    def testDasCapital(self):
        from musicbrainz2 import wsxml

        path = os.path.join(os.path.dirname(__file__),
            'release.08397059-86c1-463b-8ed0-cd596dbd174f.xml')
        handle = open(path, "rb")

        reader = wsxml.MbXmlParser()
        wsMetadata = reader.parse(handle)
        release = wsMetadata.getRelease()
        metadata = musicbrainz._getMetadata(release)

        # FIXME: 2 seconds longer than the duration according to table
        self.assertEquals(metadata.duration, 2315730)
