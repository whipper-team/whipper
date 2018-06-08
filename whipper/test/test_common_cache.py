# -*- Mode: Python; test-case-name: whipper.test.test_common_cache -*-
# vi:si:et:sw=4:sts=4:ts=4

import os

from whipper.common import cache

from whipper.test import common as tcommon


class ResultCacheTestCase(tcommon.TestCase):

    def setUp(self):
        self.cache = cache.ResultCache(
            os.path.join(os.path.dirname(__file__), 'cache', 'result'))

    def testGetResult(self):
        result = self.cache.getRipResult('fe105a11')
        self.assertEqual(result.object.title, "The Writing's on the Wall")

    def testGetIds(self):
        ids = self.cache.getIds()
        self.assertEqual(ids, ['fe105a11'])
