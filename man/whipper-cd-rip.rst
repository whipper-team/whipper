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
| - %d: release title (with disambiguation)
| - %D: disc title (without disambiguation)
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
