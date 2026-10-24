# Drive-offset source snapshot

`driveoffsets.html.gz` was retrieved from
https://www.accuraterip.com/driveoffsets.htm on 2026-09-22. It is retained
as a lossless gzip snapshot so the generated candidate table can be reproduced offline:

```sh
python3 misc/gen_drive_offsets.py \
    --input misc/accuraterip/driveoffsets.html.gz \
    --output whipper/common/drive_offsets_data.py
```

The generated module records the source URL, SHA-256 checksum, and parsed
row count. Duplicate full names and offsets have their submission counts
summed. Conflicting offsets remain separate candidates, ordered by decreasing
count and then increasing numeric offset. Names are normalized only for case
and whitespace; there are no product-token matches or manual overrides.

These are published observations. Comparing generated rows with the snapshot
checks transcription and generation; it does not independently validate each
drive. Whipper still confirms candidate offsets using the disc's AccurateRip
track checksums before storing an offset. No table download occurs at runtime.
