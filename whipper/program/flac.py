from subprocess import check_call, CalledProcessError

import logging
logger = logging.getLogger(__name__)


def encode(infile, outfile):
    """Encode infile to outfile, with flac.

    Uses ``-f`` because whipper already creates the file.

    :param infile: full path to input audio track.
    :type infile: str
    :param outfile: full path to output audio track.
    :type outfile: str
    :raises CalledProcessError: if the flac encoder returns non-zero.
    """
    try:
        # TODO: Replace with Popen so that we can catch stderr and write it to
        # logging
        check_call(['flac', '--silent', '--verify', '-o', outfile,
                    '-f', infile])
    except CalledProcessError:
        logger.exception('flac failed')
        raise
