# -*- Mode: Python; test-case-name: whipper.test.test_image_cue -*-
# vi:si:et:sw=4:sts=4:ts=4

import os
import tempfile

import unittest

from whipper.common import renamer


class RenameInFileTestcase(unittest.TestCase):

    def setUp(self):
        (fd, self._path) = tempfile.mkstemp(suffix='.whipper.renamer.infile')
        os.write(fd, 'This is a test\nThis is another\n'.encode())
        os.close(fd)

    def testVerify(self):
        o = renamer.RenameInFile(self._path, 'is is a', 'at was some')
        self.assertEqual(o.verify(), None)
        os.unlink(self._path)
        self.assertRaises(AssertionError, o.verify)

    def testDo(self):
        o = renamer.RenameInFile(self._path, 'is is a', 'at was some')
        o.do()
        with open(self._path) as f:
            output = f.read()
        self.assertEqual(output, 'That was some test\nThat was somenother\n')
        os.unlink(self._path)

    def testSerialize(self):
        o = renamer.RenameInFile(self._path, 'is is a', 'at was some')
        data = o.serialize()
        o2 = renamer.RenameInFile.deserialize(data)
        o2.do()
        with open(self._path) as f:
            output = f.read()
        self.assertEqual(output, 'That was some test\nThat was somenother\n')
        os.unlink(self._path)


class RenameFileTestcase(unittest.TestCase):

    def setUp(self):
        (fd, self._source) = tempfile.mkstemp(suffix='.whipper.renamer.file')
        os.write(fd, 'This is a test\nThis is another\n'.encode())
        os.close(fd)
        (fd, self._destination) = tempfile.mkstemp(
            suffix='.whipper.renamer.file')
        os.close(fd)
        os.unlink(self._destination)
        self._operation = renamer.RenameFile(self._source, self._destination)

    def testVerify(self):
        self.assertEqual(self._operation.verify(), None)

        handle = open(self._destination, 'w')
        handle.close()
        self.assertRaises(AssertionError, self._operation.verify)

        os.unlink(self._destination)
        self.assertEqual(self._operation.verify(), None)

        os.unlink(self._source)
        self.assertRaises(AssertionError, self._operation.verify)

    def testDo(self):
        self._operation.do()
        with open(self._destination) as f:
            output = f.read()
        self.assertEqual(output, 'This is a test\nThis is another\n')
        os.unlink(self._destination)

    def testSerialize(self):
        data = self._operation.serialize()
        o = renamer.RenameFile.deserialize(data)
        o.do()
        with open(self._destination) as f:
            output = f.read()
        self.assertEqual(output, 'This is a test\nThis is another\n')
        os.unlink(self._destination)


class OperatorTestCase(unittest.TestCase):

    def setUp(self):
        self._statePath = tempfile.mkdtemp(suffix='.whipper.renamer.operator')
        self._operator = renamer.Operator(self._statePath, 'test')

        (fd, self._source) = tempfile.mkstemp(
            suffix='.whipper.renamer.operator')
        os.write(fd, 'This is a test\nThis is another\n'.encode())
        os.close(fd)
        (fd, self._destination) = tempfile.mkstemp(
            suffix='.whipper.renamer.operator')
        os.close(fd)
        os.unlink(self._destination)
        self._operator.addOperation(
            renamer.RenameInFile(self._source, 'is is a', 'at was some'))
        self._operator.addOperation(
            renamer.RenameFile(self._source, self._destination))

    def tearDown(self):
        os.system('rm -rf %s' % self._statePath)

    def testLoadNoneDone(self):
        self._operator.save()

        o = renamer.Operator(self._statePath, 'test')
        o.load()

        self.assertEqual(o._todo, self._operator._todo)
        self.assertEqual(o._done, [])
        os.unlink(self._source)

    def testLoadOneDone(self):
        self.assertEqual(len(self._operator._done), 0)
        self._operator.save()
        next(self._operator)
        self.assertEqual(len(self._operator._done), 1)

        o = renamer.Operator(self._statePath, 'test')
        o.load()

        self.assertEqual(len(o._done), 1)
        self.assertEqual(o._todo, self._operator._todo)
        self.assertEqual(o._done, self._operator._done)

        # now continue
        next(o)
        self.assertEqual(len(o._done), 2)
        os.unlink(self._destination)

    def testLoadOneInterrupted(self):
        self.assertEqual(len(self._operator._done), 0)
        self._operator.save()

        # cheat by doing a task without saving
        self._operator._todo[0].do()

        self.assertEqual(len(self._operator._done), 0)

        o = renamer.Operator(self._statePath, 'test')
        o.load()

        self.assertEqual(len(o._done), 0)
        self.assertEqual(o._todo, self._operator._todo)
        self.assertEqual(o._done, self._operator._done)

        # now continue, resuming
        next(o)
        self.assertEqual(len(o._done), 1)
        next(o)
        self.assertEqual(len(o._done), 2)

        os.unlink(self._destination)
