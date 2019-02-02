from subprocess import Popen, PIPE

import logging
logger = logging.getLogger(__name__)

ARB = 'accuraterip-checksum'
FLAC = 'flac'


def _execute(cmd, **redirects):
    logger.debug('executing %r', cmd)
    return Popen(cmd, **redirects)


def accuraterip_checksum(f, track_number, total_tracks, wave=False, v2=False):
    v = '--accuraterip-v1'
    if v2:
        v = '--accuraterip-v2'

    track_number, total_tracks = str(track_number), str(total_tracks)

    if wave:
        cmd = [ARB, v, f, track_number, total_tracks]
        redirects = dict(stdout=PIPE, stderr=PIPE)
    else:
        flac = _execute([FLAC, '-cds', f], stdout=PIPE)
        cmd = [ARB, v, '/dev/stdin', track_number, total_tracks]
        redirects = dict(stdin=flac.stdout, stdout=PIPE, stderr=PIPE)
    arc = _execute(cmd, **redirects)

    if not wave:
        flac.stdout.close()

    out, _ = arc.communicate()

    if not wave:
        flac.wait()
        if flac.returncode != 0:
            logger.warning('ARC calculation failed: flac '
                           'return code is non zero: %r', flac.returncode)
            return None

    if arc.returncode != 0:
        logger.warning('ARC calculation failed: '
                       'arc return code is non zero: %r', arc.returncode)
        return None

    try:
        checksum = int('0x%s' % out.strip(), base=16)
        logger.debug('returned %r', checksum)
        return checksum
    except ValueError:
        logger.warning('ARC output is not usable')
        return None
