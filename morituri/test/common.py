# -*- Mode: Python -*-
# vi:si:et:sw=4:sts=4:ts=4

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
