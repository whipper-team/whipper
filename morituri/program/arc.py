import logging
from subprocess import Popen, PIPE
from os.path import exists

ARB = 'accuraterip-checksum'
FLAC = 'flac'

def accuraterip_checksum(f, track, tracks, wave=False, v2=False):
    v = '--accuraterip-v1'
    if v2:
        v = '--accuraterip-v2'

    track, tracks = str(track), str(tracks)

    if not wave:
        flac = Popen([FLAC, '-cds', f], stdout=PIPE)

        arc = Popen([ARB, v, '/dev/stdin', track, tracks],
                    stdin=flac.stdout, stdout=PIPE, stderr=PIPE)
    else:
        arc = Popen([ARB, v, f, track, tracks],
                    stdout=PIPE, stderr=PIPE)

    if not wave:
        flac.stdout.close()

    out, err = arc.communicate()

    if not wave:
        flac.wait()
        flac_rc = flac.returncode

    arc_rc = arc.returncode

    if not wave and flac_rc != 0:
        logging.warning('ARC calculation failed: flac return code is non zero')
        return None

    if arc_rc != 0:
        logging.warning('ARC calculation failed: arc return code is non zero')
        return None

    out = out.strip()
    try:
        outh = int('0x%s' % out, base=16)
    except ValueError:
        logging.warning('ARC output is not usable')
        return None

    return outh
