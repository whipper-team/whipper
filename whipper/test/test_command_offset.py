# -*- Mode: Python; test-case-name: whipper.test.test_command_offset -*-
# vi:si:et:sw=4:sts=4:ts=4

import argparse
import sys
import types

# The offset command only needs argument parsing for these tests, but importing
# it pulls in platform-specific helpers. Stub the ones that do not exist on
# every platform so the tests run anywhere the suite runs.
try:
    from fcntl import ioctl  # noqa: F401
except ImportError:
    _fcntl = types.ModuleType("fcntl")
    _fcntl.ioctl = lambda *args, **kwargs: 0  # noqa: E731
    sys.modules["fcntl"] = _fcntl

try:
    import accuraterip  # noqa: F401
except ImportError:
    _stub = types.ModuleType("accuraterip")
    _stub.compute = lambda *args, **kwargs: (0, 0)  # noqa: E731
    sys.modules.setdefault("accuraterip", _stub)

from whipper.command.offset import Find, OFFSETS  # noqa: E402

from whipper.test import common as tcommon  # noqa: E402


class FindOffsetsTestCase(tcommon.TestCase):

    def _find(self, offsets):
        cmd = Find.__new__(Find)
        cmd.parser = argparse.ArgumentParser(prog="whipper offset find")
        cmd.parser.add_argument("-o", "--offsets", default=OFFSETS)
        cmd.options = cmd.parser.parse_args(["--offsets", offsets])
        return cmd

    def testValidOffsetsAndRanges(self):
        cmd = self._find("1,2,4:6")
        cmd.handle_arguments()
        self.assertEqual(cmd._offsets, [1, 2, 4, 5, 6])

    def testInvalidOffsetsIsUsageError(self):
        cmd = self._find("abc")
        try:
            cmd.handle_arguments()
        except SystemExit as e:
            self.assertEqual(e.code, 2)
        else:
            self.fail("handle_arguments did not exit on invalid offsets")

    def testInvalidRangeIsUsageError(self):
        cmd = self._find("1:2:3")
        try:
            cmd.handle_arguments()
        except SystemExit as e:
            self.assertEqual(e.code, 2)
        else:
            self.fail("handle_arguments did not exit on invalid range")
