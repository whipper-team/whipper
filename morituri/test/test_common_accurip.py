# -*- Mode: Python; test-case-name: morituri.test.test_common_accurip -*-
# vi:si:et:sw=4:sts=4:ts=4

import os

from morituri.common import accurip

from morituri.test import common as tcommon


class AccurateRipResponseTestCase(tcommon.TestCase):

    def testResponse(self):
        path = os.path.join(os.path.dirname(__file__),
            'dBAR-011-0010e284-009228a3-9809ff0b.bin')
        data = open(path, "rb").read()

        responses = accurip.getAccurateRipResponses(data)
        self.assertEquals(len(responses), 3)


        response = responses[0]

        self.assertEquals(response.trackCount, 11)
        self.assertEquals(response.discId1, "0010e284")
        self.assertEquals(response.discId2, "009228a3")
        self.assertEquals(response.cddbDiscId, "9809ff0b")

        for i in range(11):
            self.assertEquals(response.confidences[i], 35)
        self.assertEquals(response.checksums[0], "beea32c8")
        self.assertEquals(response.checksums[10], "acee98ca")
