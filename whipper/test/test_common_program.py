# -*- Mode: Python; test-case-name: whipper.test.test_common_program -*-
# vi:si:et:sw=4:sts=4:ts=4


import os
import pickle

import unittest

from whipper.result import result
from whipper.common import program, accurip, mbngs, config
from whipper.command.cd import DEFAULT_DISC_TEMPLATE


class PathTestCase(unittest.TestCase):

    def testStandardTemplateEmpty(self):
        prog = program.Program(config.Config())

        path = prog.getPath(u'/tmp', DEFAULT_DISC_TEMPLATE,
                            'mbdiscid', None)
        self.assertEquals(path,
                          unicode('/tmp/unknown/Unknown Artist - mbdiscid/'
                                  'Unknown Artist - mbdiscid'))

    def testStandardTemplateFilled(self):
        prog = program.Program(config.Config())
        md = mbngs.DiscMetadata()
        md.artist = md.sortName = 'Jeff Buckley'
        md.title = 'Grace'

        path = prog.getPath(u'/tmp', DEFAULT_DISC_TEMPLATE,
                            'mbdiscid', md, 0)
        self.assertEquals(path,
                          unicode('/tmp/unknown/Jeff Buckley - Grace/'
                                  'Jeff Buckley - Grace'))

    def testIssue66TemplateFilled(self):
        prog = program.Program(config.Config())
        md = mbngs.DiscMetadata()
        md.artist = md.sortName = 'Jeff Buckley'
        md.title = 'Grace'

        path = prog.getPath(u'/tmp', u'%A/%d', 'mbdiscid', md, 0)
        self.assertEquals(path,
                          u'/tmp/Jeff Buckley/Grace')
