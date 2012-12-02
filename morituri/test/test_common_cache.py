# -*- Mode: Python; test-case-name: morituri.test.test_common_cache -*-
# vi:si:et:sw=4:sts=4:ts=4

import os

from morituri.common import cache

from morituri.test import common as tcommon


class ResultCacheTestCase(tcommon.TestCase):

    def setUp(self):
        self.cache = cache.ResultCache(
            os.path.join(os.path.dirname(__file__), 'cache', 'result'))

    def testGetResult(self):
        result = self.cache.getRipResult('fe105a11')
        self.assertEquals(result.object.title, "The Writing's on the Wall")

    def testGetIds(self):
        ids = self.cache.getIds()
        self.assertEquals(ids, ['fe105a11'])
