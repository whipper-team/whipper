# -*- Mode: Python; test-case-name: morituri.test.test_image_toc -*-
# vi:si:et:sw=4:sts=4:ts=4

import os
import unittest

from morituri.image import toc

def h(i):
    return "0x%08x" % i

class LadyhawkeTestCase(unittest.TestCase):
    # Ladyhawke - Ladyhawke - 0602517818866
    # contains 12 audio tracks and one data track
    # CDDB has been verified against freedb:
    #   http://www.freedb.org/freedb/misc/c60af50d
    #   http://www.freedb.org/freedb/jazz/c60af50d
    # AccurateRip URL has been verified against EAC's, using wireshark

    def setUp(self):
        self.toc = toc.TOC([
            toc.Track( 1,      0,  15536),
            toc.Track( 2,  15537,  31690),
            toc.Track( 3,  31691,  50865),
            toc.Track( 4,  50866,  66465),
            toc.Track( 5,  66466,  81201),
            toc.Track( 6,  81202,  99408),
            toc.Track( 7,  99409, 115919),
            toc.Track( 8, 115920, 133092),
            toc.Track( 9, 133093, 149846),
            toc.Track(10, 149847, 161559),
            toc.Track(11, 161560, 177681),
            toc.Track(12, 177682, 195705),
            toc.Track(13, 207106, 210384, audio=False),
        ])

    def testCDDB(self):
        self.assertEquals(self.toc.getCDDBDiscId(), "c60af50d")

    def testAccurateRip(self):
        self.assertEquals(self.toc.getAccurateRipIds(), (
            "0013bd5a", "00b8d489"))
