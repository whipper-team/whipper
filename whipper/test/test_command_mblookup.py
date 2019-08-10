# vi:si:et:sw=4:sts=4:ts=4:set fileencoding=utf-8
"""Tests for whipper.command.mblookup"""

import os
import pickle
import unittest

from whipper.command import mblookup


class MBLookupTestCase(unittest.TestCase):
    """Test cases for whipper.command.mblookup.MBLookup"""

    @staticmethod
    def _mock_musicbrainz(discid, country=None, record=False):
        """Mock function for whipper.common.mbngs.musicbrainz function."""
        filename = "whipper.discid.{}.pickle".format(discid)
        path = os.path.join(os.path.dirname(__file__), filename)
        with open(path) as p:
            return pickle.load(p)

    def testMissingReleaseType(self):
        """Test that lookup for release without a type set doesn't fail."""
        # Using: Gustafsson, Österberg & Cowle - What's Up? 8 (disc 4)
        # https://musicbrainz.org/release/d8e6153a-2c47-4804-9d73-0aac1081c3b1
        mblookup.musicbrainz = self._mock_musicbrainz
        discid = "xu338_M8WukSRi0J.KTlDoflB8Y-"
        # https://musicbrainz.org/cdtoc/xu338_M8WukSRi0J.KTlDoflB8Y-
        lookup = mblookup.MBLookup([discid], 'whipper mblookup', None)
        lookup.do()
