# -*- Mode: Python -*-
# vi:si:et:sw=4:sts=4:ts=4

import os
import sys

# twisted's unittests have skip support, standard unittest don't
from twisted.trial import unittest

from morituri.common import log

log.init()

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
         "%s") % (output, ))


def diffStrings(orig, new, desc='input'):

    def _tolines(s):
        return [line + '\n' for line in s.split('\n')]

    return _diff(_tolines(orig),
                 _tolines(new),
                 desc=desc)


class TestCase(log.Loggable, unittest.TestCase):
    # unittest.TestCase.failUnlessRaises does not return the exception,
    # and we'd like to check for the actual exception under TaskException,
    # so override the way twisted.trial.unittest does, without failure

    def failUnlessRaises(self, exception, f, *args, **kwargs):
        try:
            result = f(*args, **kwargs)
        except exception, inst:
            return inst
        except exception, e:
            raise self.failureException('%s raised instead of %s:\n %s'
                                        % (sys.exc_info()[0],
                                           exception.__name__,
                                           log.getExceptionMessage(e)))
        else:
            raise self.failureException('%s not raised (%r returned)'
                                        % (exception.__name__, result))

    assertRaises = failUnlessRaises


class UnicodeTestMixin:
    # A helper mixin to skip tests if we're not in a UTF-8 locale

    try:
        os.stat(u'morituri.test.B\xeate Noire.empty')
    except UnicodeEncodeError:
        skip = 'No UTF-8 locale'
    except OSError:
        pass
