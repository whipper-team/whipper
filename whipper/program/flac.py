from subprocess import check_call, CalledProcessError
import re

from whipper.common import common

import logging

logger = logging.getLogger(__name__)

FLAC = 'flac'


def encode(infile, outfile):
    """Encode infile to outfile, with flac.

    Uses ``--force`` because whipper already creates the file.

    :param infile: full path to input audio track.
    :type infile: str
    :param outfile: full path to output audio track.
    :type outfile: str
    :raises CalledProcessError: if the flac encoder returns non-zero.
    """
    try:
        # TODO: Replace with Popen so that we can catch stderr and write it to
        # logging
        check_call([FLAC, '--silent', '--verify', '-o', outfile,
                    '--force', infile])
    except CalledProcessError:
        logger.exception('flac encode failed')
        raise


def decode(infile, outfile):
    """Decode infile to outfile, with flac.

    Uses ``--force`` because whipper already creates the file.

    :param infile: full path to input audio track.
    :type infile: str
    :param outfile: full path to output audio track.
    :type outfile: str
    :raises CalledProcessError: if the flac encoder returns non-zero.
    """
    try:
        # TODO: Replace with Popen so that we can catch stderr and write it to
        # logging
        check_call([FLAC, '--silent', '--decode', '-o', outfile,
                   '--force', infile])
    except CalledProcessError:
        logger.exception('flac decode failed')
        raise


# Sample version string:
# flac 1.3.2
_VERSION_RE = re.compile(
    "^flac (?P<major>.+)\.(?P<minor>.+)\.(?P<micro>.+)")


def getVersion():
    """Detect flac's version.

    :returns: Formatted flac version string
    :rtype: string
    """
    getter = common.VersionGetter('flac',
                                  [FLAC, "--version"],
                                  _VERSION_RE,
                                  "%(major)s.%(minor)s.%(micro)s",
                                  stderr=False)
    return getter.get()
