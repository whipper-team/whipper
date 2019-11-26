import accuraterip


def accuraterip_checksum(f, track_number, total_tracks):
    return accuraterip.compute(f, track_number, total_tracks)
