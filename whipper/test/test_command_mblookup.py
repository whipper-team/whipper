# vi:si:et:sw=4:sts=4:ts=4:set fileencoding=utf-8
"""Tests for whipper.command.mblookup"""

import os
import pickle
import unittest
import json

from whipper.command import mblookup
from whipper.common.mbngs import _getMetadata


class MBLookupTestCase(unittest.TestCase):
    """Test cases for whipper.command.mblookup.MBLookup"""

    @staticmethod
    def _mock_musicbrainz(discid, country=None, record=False):
        """Mock function for whipper.common.mbngs.musicbrainz function."""
        filename = "whipper.discid.{}.pickle".format(discid)
        path = os.path.join(os.path.dirname(__file__), filename)
        with open(path, "rb") as p:
            return pickle.load(p)

    @staticmethod
    def _mock_getReleaseMetadata(release_id):
        """
        Mock function for whipper.common.mbngs.getReleaseMetadata.

        :param release_id: MusicBrainz Release ID
        :type release_id: str
        :returns: a DiscMetadata object based on the given release_id
        :rtype: `DiscMetadata`
        """
        filename = 'whipper.release.{}.json'.format(release_id)
        path = os.path.join(os.path.dirname(__file__), filename)
        with open(path, "rb") as handle:
            response = json.loads(handle.read().decode('utf-8'))
        return _getMetadata(response['release'])

    def testMissingReleaseType(self):
        """Test that lookup for release without a type set doesn't fail."""
        # Using: Gustafsson, Österberg & Cowle - What's Up? 8 (disc 4)
        # https://musicbrainz.org/release/d8e6153a-2c47-4804-9d73-0aac1081c3b1
        mblookup.musicbrainz = self._mock_musicbrainz
        discid = "xu338_M8WukSRi0J.KTlDoflB8Y-"
        # https://musicbrainz.org/cdtoc/xu338_M8WukSRi0J.KTlDoflB8Y-
        lookup = mblookup.MBLookup([discid], 'whipper mblookup', None)
        lookup.do()

    def testGetDataFromReleaseId(self):
        """Test that lookup for a release with a specified id."""
        # Using: The KLF - Space & Chill Out
        # https://musicbrainz.org/release/c56ff16e-1d81-47de-926f-ba22891bd2bd
        mblookup.getReleaseMetadata = self._mock_getReleaseMetadata
        releaseid = 'c56ff16e-1d81-47de-926f-ba22891bd2bd'
        lookup = mblookup.MBLookup([releaseid], 'whipper mblookup', None)
        lookup.do()
