import accuraterip


def accuraterip_checksum(f, track_number, total_tracks):
    return accuraterip.compute(f.encode('utf-8'), track_number, total_tracks)
