from subprocess import check_call, CalledProcessError

import logging
logger = logging.getLogger(__name__)

FLAC = 'flac'


def encode(infile, outfile):
    """
    Encodes infile to outfile, with flac.
    Uses '-f' because morituri already creates the file.
    """
    try:
        check_call(['flac', '--totally-silent', '--verify', '-o', outfile,
                    '-f', infile])
    except CalledProcessError:
        logger.exception('flac failed')
        raise
