# -*- Mode: Python; test-case-name: morituri.test.test_common_musicbrainzngs -*-
# vi:si:et:sw=4:sts=4:ts=4

import os
import json

import unittest

from morituri.common import musicbrainzngs


class MetadataTestCase(unittest.TestCase):

    def testJeffEverybodySingle(self):
        path = os.path.join(os.path.dirname(__file__),
            'morituri.release.3451f29c-9bb8-4cc5-bfcc-bd50104b94f8.json')
        handle = open(path, "rb")
        response = json.loads(handle.read())
        handle.close()
        discid = "wbjbST2jUHRZaB1inCyxxsL7Eqc-"

        metadata = musicbrainzngs._getMetadata(response['release'], discid)

        self.failIf(metadata.release)
