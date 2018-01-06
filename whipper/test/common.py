# -*- Mode: Python -*-
# vi:si:et:sw=4:sts=4:ts=4

import re
import os
import sys

import whipper

# twisted's unittests have skip support, standard unittest don't
from twisted.trial import unittest

# lifted from flumotion


def _diff(old, new, desc):
    import difflib
    lines = difflib.unified_diff(old, new)
    lines = list(lines)
    if not lines:
        return
    output = ''
    for line in lines:
        output += '%s: %s\n' % (desc, line[:-1])

    raise AssertionError(
        ("\nError while comparing strings:\n"
         "%s") % (output.encode('utf-8'), ))


def diffStrings(orig, new, desc='input'):

    assert type(orig) == type(new), 'type %s and %s are different' % (
        type(orig), type(new))

    def _tolines(s):
        return [line + '\n' for line in s.split('\n')]

    return _diff(_tolines(orig),
                 _tolines(new),
                 desc=desc)


class TestCase(unittest.TestCase):
    # unittest.TestCase.failUnlessRaises does not return the exception,
    # and we'd like to check for the actual exception under TaskException,
    # so override the way twisted.trial.unittest does, without failure

    def failUnlessRaises(self, exception, f, *args, **kwargs):
        try:
            result = f(*args, **kwargs)
        except exception as inst:
            return inst
        except exception as e:
            raise Exception('%s raised instead of %s:\n %s' %
                            (sys.exec_info()[0], exception.__name__, str(e))
                            )
        else:
            raise Exception('%s not raised (%r returned)' %
                            (exception.__name__, result)
                            )

    assertRaises = failUnlessRaises

    def readCue(self, name):
        """Read a cue file and replace its version number with the current one.

        The version number is replaced to use the cue file in comparisons.

        :param name: cuesheet filename (without path).
        :type name: str
        :returns: the cuesheet with version number replaced.
        :rtype: str
        """
        cuefile = os.path.join(os.path.dirname(__file__), name)
        ret = open(cuefile).read().decode('utf-8')
        ret = re.sub(
            'REM COMMENT "whipper.*',
            'REM COMMENT "whipper %s"' % (whipper.__version__),
            ret, re.MULTILINE)

        return ret


class UnicodeTestMixin:
    # A helper mixin to skip tests if we're not in a UTF-8 locale

    try:
        os.stat(u'whipper.test.B\xeate Noire.empty')
    except UnicodeEncodeError:
        skip = 'No UTF-8 locale'
    except OSError:
        pass
