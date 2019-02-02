# -*- Mode: Python; test-case-name: whipper.test.test_common_program -*-
# vi:si:et:sw=4:sts=4:ts=4


import unittest

from whipper.common import program, mbngs, config
from whipper.command.cd import DEFAULT_DISC_TEMPLATE


class PathTestCase(unittest.TestCase):

    def testStandardTemplateEmpty(self):
        prog = program.Program(config.Config())

        path = prog.getPath(u'/tmp', DEFAULT_DISC_TEMPLATE,
                            'mbdiscid', None)
        self.assertEqual(path, (u'/tmp/unknown/Unknown Artist - mbdiscid/'
                                u'Unknown Artist - mbdiscid'))

    def testStandardTemplateFilled(self):
        prog = program.Program(config.Config())
        md = mbngs.DiscMetadata()
        md.artist = md.sortName = 'Jeff Buckley'
        md.title = 'Grace'

        path = prog.getPath(u'/tmp', DEFAULT_DISC_TEMPLATE,
                            'mbdiscid', md, 0)
        self.assertEqual(path, (u'/tmp/unknown/Jeff Buckley - Grace/'
                                u'Jeff Buckley - Grace'))

    def testIssue66TemplateFilled(self):
        prog = program.Program(config.Config())
        md = mbngs.DiscMetadata()
        md.artist = md.sortName = 'Jeff Buckley'
        md.title = 'Grace'

        path = prog.getPath(u'/tmp', u'%A/%d', 'mbdiscid', md, 0)
        self.assertEqual(path,
                         u'/tmp/Jeff Buckley/Grace')
