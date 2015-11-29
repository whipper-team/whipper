FORK INFORMATIONS
---------
The name of this fork is still to be decided, right now I'll be using whipper.

This branch is very close to morituri's master one (the internal 'morituri' references are still unchanged), I've just merged the following commits:
- [#79](https://github.com/thomasvs/morituri/issues/79)
- [#92](https://github.com/thomasvs/morituri/issues/92)
- [#109](https://github.com/thomasvs/morituri/issues/109)
- [#133](https://github.com/thomasvs/morituri/issues/133) (with custom `.travis.yml`)
- [#137](https://github.com/thomasvs/morituri/issues/137)
- [#139](https://github.com/thomasvs/morituri/issues/139)
- [#140](https://github.com/thomasvs/morituri/issues/140)
- [#141](https://github.com/thomasvs/morituri/issues/141)

And changed the default logger to the morituri-whatlogger's one.

WHIPPER [![Build Status](https://travis-ci.org/JoeLametta/morituri.svg?branch=fork)](https://travis-ci.org/JoeLametta/morituri)
---------
whipper is a fork of the morituri project (CDDA ripper, for *nix systems, aiming for accuracy over speed).

It improves morituri which development seems to have halted/slowed down merging old pull requests and improving it with new functions.

If possible, I'll try to mainline the useful commits of this fork but, in the future, this may not be possible because of different project choices.

The home page is still TBD.

RATIONALE
---------
For a more detailed rationale, see morituri's wiki page ['The Art of the Rip'](
http://thomas.apestaart.org/thomas/trac/wiki/DAD/Rip).

FEATURES
--------
* support for MusicBrainz for metadata lookup
* support for AccurateRip (V1) verification
* detects sample read offset and ability to defeat cache of drives
* performs test and copy rip
* detects and rips Hidden Track One Audio (only if not digitally silent)
* templates for file and directory naming
* support for lossless encoding and lossy encoding or re-encoding of images
* tagging using GStreamer, including embedding MusicBrainz id's
* retagging of images
* plugins for logging
* for now, only a command line client (rip) is shipped

REQUIREMENTS
------------
- cdparanoia, for the actual ripping
- cdrdao, for session, TOC, pregap, and ISRC extraction
- GStreamer and its python bindings, for encoding
  - gstreamer0.10-base-plugins >= 0.10.22 for appsink
  - gstreamer0.10-good-plugins for wav encoding (it depends on the Linux distro used)
- python musicbrainz2, for metadata lookup
- python-setuptools, for plugin support
- python-cddb, for showing but not using disc info if not in MusicBrainz
- pycdio, for drive identification (optional)
  - Required for drive offset and caching behavior to be stored in the config file

Additionally, if you're building from a git checkout:
- autoconf
- automake

GETTING WHIPPER
----------------
If you are building from a source tarball or checkout, you can choose to
use whipper installed or uninstalled.

- getting:
    - Change to a directory where you want to put the whipper source code
      (For example, `$HOME/dev/ext` or `$HOME/prefix/src`)
    - source: download tarball, unpack, and change to its directory
    - checkout:

            git clone -b fork --single-branch git://github.com/JoeLametta/morituri.git
            cd morituri
            git submodule init
            git submodule update
            ./autogen.sh

- building:

        ./configure
        make

- you can now choose to install it or run it uninstalled.

    - installing:

            make install

    - running uninstalled:

            ln -sf `pwd`/misc/morituri-uninstalled $HOME/bin/morituri-git
            morituri-git  # this drops you in a shell where everything is set up to use whipper

RUNNING WHIPPER
----------------
whipper currently only has a command-line interface called 'rip'

rip is self-documenting.
`rip -h` gives you the basic instructions.

rip implements a tree of commands; for example, the top-level 'changelog'
command has a number of sub-commands.

Positioning of arguments is important;

    rip cd -d (device) rip

is correct, while

    rip cd rip -d (device)

is not, because the `-d` argument applies to the rip command.

Check the man page (rip(1)) for more information.


RUNNING UNINSTALLED
-------------------
To make it easier for developers, you can run whipper straight from the
source checkout:

    ./autogen.sh
    make
    misc/morituri-uninstalled

GETTING STARTED
---------------
The simplest way to get started making accurate rips is:

- pick a relatively popular CD that has a good change of being in the
  AccurateRip database
- find the drive's offset by running

        rip offset find

- wait for it to complete; this might take a while
- optionally, confirm this offset with two more discs
- analyze the drive's caching behaviour

        rip drive analyze

- rip the disc by running one of

        rip cd rip  # uses the offset from configuration file
        rip cd rip --offset (the number you got before)  # manually specified offset

FILING BUGS
-----------
whipper's bug tracker is still TBD.

morituri's bug tracker is at [http://thomas.apestaart.org/morituri/trac/](
http://thomas.apestaart.org/morituri/trac/).
When filing bugs, please run the failing command with the environment variable
`RIP_DEBUG` set; for example:

    RIP_DEBUG=5 rip offset find > morituri.log 2>&1
    gzip morituri.log

And attach the gzipped log file to your bug report.

KNOWN ISSUES
------------
- no GUI yet
- only AccurateRip V1 CRCs are computed and checked against the online database
- `rip offset find` fails to delete the temporary .wav files it creates if an error occurs while ripping
- morituri detects the pre-emphasis flag in the TOC but doesn't add it to the cue sheet
  - To improve the accuracy of the detection, the sub-channel data should be scanned too
- cd-text isn't read from the CD (useful when the CD informations are not available in the MusicBrainz DB)

GOALS
-----
- quality over speed
- support one-command automatic ripping
- support offline ripping (doing metadata lookup and log rewriting later)
  - separate the info/result about the rip from the metadata/file generation/...

CONFIGURATION FILE
------------------
The configuration file is stored according to [XDG Base Directory Specification](
http://standards.freedesktop.org/basedir-spec/basedir-spec-latest.html)
when possible.

It lives in `$XDG_CONFIG_HOME/morituri/morituri.conf`

The configuration file follows python's ConfigParser syntax.

The possible sections are:

- main section: [main]
  - `path_filter_fat`: whether to filter path components for FAT file systems
  - `path_filter_special`: whether to filter path components for special
                           characters

- drive section: [drive:IDENTIFIER], one for each configured drive
  All these values are probed by morituri and should not be edited by hand.
  - `defeats_cache`: whether this drive can defeat the audio cache
  - `read_offset`: the read offset of the drive

- rip command section: [rip.COMMAND.SUBCOMMAND]
  Can be used to change the command options default values.

Example section to configure "rip cd rip" defaults:

   [rip.cd.rip]
    unknown = True
    output_directory = ~/My Music
    track_template = new/%%A/%%y - %%d/%%t - %%n
    disc_template = %(track_template)s
    profile = flac

Note: to get a literal '%' character it must be doubled.

CONTRIBUTING
------------
- Please send pull requests through GitHub.
