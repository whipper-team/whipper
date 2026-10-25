==============
whipper-cd-rip
==============

---------
Rips a CD
---------

:Author: Louis-Philippe Véronneau
:Date: 2021
:Manual section: 1

Synopsis
========

| whipper cd rip [**options**]
| whipper cd rip **-h**

Options
=======

| **-h** | **--help**
|     Show this help message and exit

| **-R** *<RELEASE_ID>* | **--release-id** *<RELEASE_ID>*
|     MusicBrainz release id to match to (if there are multiple)

| **-p** | **--prompt**
|     Prompt if there are multiple matching releases

| **-c** *<COUNTRY>* | **--country** *<COUNTRY>*
|     Filter releases by country

| **-L** *<LOGGER<* | **--logger** *<LOGGER>*
|     Logger to use

| **-o** *<OFFSET>* | **--offset** *<OFFSET>*
|     Sample read offset

| **-x** | **--force-overread**
|     Force overreading into the lead-out portion of the disc. Works only if
|     the patched cdparanoia package is installed and the drive supports this
|     feature

| **-O** *<OUTPUT_DIRECTORY>* | **--output-directory** *<OUTPUT_DIRECTORY>*
|     Output directory; will be included in file paths in log

| **-W** *<WORKING_DIRECTORY>* | **--working-directory** *<WORKING_DIRECTORY>*
|     Working directory; whipper will change to this directory and files will
|     be created relative to it when not absolute

| **--track-template** *<TRACK_TEMPLATE>*
|     Template for track file naming

| **--disc-template** *<DISC_TEMPLATE>*
|     Template for disc file naming

| **-U** | **--unknown**
|     whether to continue ripping if the CD is unknown

| **--cdr**
|     whether to continue ripping if the disc is a CD-R

| **-C** | **--cover-art** *file embed complete*
|     Fetch cover art and save it as standalone file, embed into FLAC files or
|     perform both actions: file, embed, complete option values respectively

| **-r** | **--max-retries** *<RETRIES>*
|     Number of rip attempts before giving up if can't rip a track. This
|     defaults to 5; 0 means infinity.

| **-k** | **--keep-going**
|     continue ripping further tracks instead of giving up if a track can't be
|     ripped

Partial rips
============

A failed or interrupted read preserves previously completed audio and writes
recovery diagnostics to ``<disc>.partial.log``. Only an attempt completing all
requested audio tracks writes the ordinary ``<disc>.log`` used to identify a
finished rip. ``--keep-going`` still returns an error if any audio track fails.
Missing test or copy CRCs never qualify as a successful copy.

Partial cue sheets and playlists reference only completed audio. Cue track
numbers retain their disc numbering. ``REM ORIGINAL_TRACK`` comments record
the original sector boundaries and pregap lengths. When pregap audio is
unavailable, ``REM UNAVAILABLE_PREGAP`` records it without synthesizing silence.
A completed HTOA file remains in the playlist and diagnostics if track 1 fails;
it cannot form a playable cue track without inventing an INDEX 01 for track 1.
Partial cues describe the available files, not a complete disc image, and are
not submitted for full-disc AccurateRip verification.

The partial log remains as a record of the earlier attempt after recovery.
Resume still uses the existing audio validation gate. When integrating #707,
retain its decoded sample-count, format and CRC checks before reusing audio;
CRC equality alone does not establish a complete audio file. The separate
finished-log check in #704 must reject incomplete logs: the internal partial
log omits both finished-log markers (EOF and the ordinary hash label),
as well as using a separate filename.

Template schemes
================

| Tracks are named according to the track template, filling in the variables
| and adding the file extension. Variables exclusive to the track template are:

|

| - %t: track number
| - %a: track artist
| - %n: track title
| - %s: track sort name

| Disc files (.cue, .log, .m3u) are named according to the disc template,
| filling in the variables and adding the file extension. Variables for both
| disc and track template are:

|

| - %A: release artist
| - %S: release sort name
| - %B: release barcode
| - %C: release catalog number
| - %c: release disambiguation comment
| - %d: release title (with disambiguation)
| - %D: disc title (without disambiguation)
| - %I: MusicBrainz Disc ID
| - %M: total number of discs in the chosen release
| - %N: number of current disc
| - %T: medium title
| - %y: release year
| - %r: release type, lowercase
| - %R: release type, normal case
| - %x: audio extension, lowercase
| - %X: audio extension, uppercase

| Paths to track files referenced in .cue and .m3u files will be made
| relative to the directory of the disc files.

| All files will be created relative to the given output directory.
| Log files will log the path to tracks relative to this directory

See Also
========

whipper(1), whipper-cd(1), whipper-cd-info(1)
