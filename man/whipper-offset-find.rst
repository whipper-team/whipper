===================
whipper-offset-find
===================

--------------------------------------------------------------------------------
Find drive's read offset by ripping tracks from a CD in the AccurateRip database
--------------------------------------------------------------------------------

:Author: Louis-Philippe Véronneau
:Date: 2020
:Manual section: 1

Synopsis
========

| whipper offset find [**-o** *<OFFSETS>*] [**-d** *<DEVICE>*]
|                     [**--no-frame450**] [**--no-prioritize-known**]
|                     [**--read-timeout** *<SECONDS>*]
|                     [**--read-idle-timeout** *<SECONDS>*]
| whipper offset find **-h**

Options
=======

| **-h** | **--help**
|     Show this help message and exit

| **-o** *<OFFSETS>* | **--offsets** *<OFFSETS>*
|     Probe only these offsets, in order; commas separate values and colons
|     specify inclusive ranges. Bypasses automatic candidate selection.

| **-d** *<DEVICE>* | **--device** *<DEVICE>*
|     Path to the CD-DA device

| **--no-frame450**
|     Skip the short AccurateRip checksum window and use full-track probes.

| **--no-prioritize-known**
|     Do not prioritize configured or published drive-model offsets in the probe
|     list. Combine with **--no-frame450** for the original probing order.

| **--read-timeout** *<SECONDS>*
|     Maximum total time for each offset window or full-track confirmation
|     read. Default: 1800 seconds. Must be positive and finite.

| **--read-idle-timeout** *<SECONDS>*
|     Maximum time without forward read/write progress or output growth.
|     Default: 120 seconds. Must be positive and finite. Repeated progress
|     messages and read errors do not reset this limit.

Detection
=========

Without **--offsets**, whipper reads a short window around frame 450 of track 1
and searches within 3,000 samples of the configured offset, the most frequently
reported model offset, or zero if neither is available. It confirms suggested
offsets with the AccurateRip checksums of every track except the last. The
existing minimum of three tracks and configuration format are unchanged.
When several offsets match the short window, configured and published offsets
are tried first among those matches, unless **--no-prioritize-known** is set.

If window data is unavailable or candidates fail confirmation, ordinary probing
continues, trying configured and published offsets before the existing list.
Model names must match completely, ignoring case and whitespace. Conflicting
published offsets remain candidates; a lookup never bypasses confirmation.
No drive-table download is made at runtime.

On timeout, whipper terminates the reader, escalating to a kill if necessary,
reaps it, and removes the temporary WAV. A window timeout falls back to ordinary
probing; a confirmation timeout rejects the candidate and tries the next offset.
An offset is saved only after full-track confirmation succeeds for every required
track. Increase the limits for particularly slow drives. Limits apply to each
read, so the complete search may take longer. They do not apply to ordinary
album ripping. If the operating system cannot reap a killed reader within the
cleanup grace period, the search stops instead of starting another read.

See Also
========

whipper(1), whipper-offset(1)
