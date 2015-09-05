morituri is a CD ripper aiming for accuracy over speed for UNIX systems.
Its features are modeled to compare with Exact Audio Copy on Windows.
The home page is https://thomas.apestaart.org/morituri/trac/


RATIONALE
---------
For a more detailed rationale, see my wiki page ['The Art of the Rip'](
https://thomas.apestaart.org/thomas/trac/wiki/DAD/Rip).

FEATURES
--------
* support for MusicBrainz for metadata lookup
* support for AccurateRip (V1) verification
* detects sample read offset and ability to defeat cache of drives
* performs test and copy rip
* detects and rips Hidden Track One Audio
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
  - gst-plugins-base >= 0.10.22 for appsink
- python musicbrainz2, for metadata lookup
- python-setuptools, for plugin support
- python-cddb, for showing but not using disc info if not in musicbrainz
- pycdio, for drive identification (optional)
  - Required for drive offset and caching behaviour to be stored in the config file

Additionally, if you're building from a git checkout:
- autoconf
- automake

GETTING MORITURI
----------------
If you are building from a source tarball or checkout, you can choose to
use morituri installed or uninstalled.

- getting:
    - Change to a directory where you want to put the morituri source code
      (For example, `$HOME/dev/ext` or `$HOME/prefix/src`)
    - source: download tarball, unpack, and change to its directory
    - checkout:

            git clone git://github.com/thomasvs/morituri.git
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
            morituri-git  # this drops you in a shell where everything is set up to use morituri

RUNNING MORITURI
----------------
morituri currently only has a command-line interface called 'rip'

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

To make it easier for developers, you can run morituri straight from the
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
morituri's bug tracker is at [https://thomas.apestaart.org/morituri/trac/](
https://thomas.apestaart.org/morituri/trac/).
When filing bugs, please run the failing command with the environment variable
`RIP_DEBUG` set; for example:

    RIP_DEBUG=5 rip offset find > morituri.log 2>&1
    gzip morituri.log

And attach the gzipped log file to your bug report.

KNOWN ISSUES
------------
- no GUI yet
- only AccurateRip V1 CRCs are computed and checked against the online database
- `rip offset find` fails to delete the temporary .wav files it creates if error occurs while ripping (thomasvs/morituri#75)
- morituri detects the pre-emphasis flag in the TOC but doesn't add it to the cue sheet
  - To improve the accuracy of the detection the sub-channel data should be scanned too
- CD-Text is not used when ripping CDs not available in MusicBrainz DB

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
There is a "main" section and zero or more sections starting with "drive:"

- main section:
  - `path_filter_fat`: whether to filter path components for FAT file systems
  - `path_filter_special`: whether to filter path components for special
                           characters

- drive section:
  All these values are probed by morituri and should not be edited by hand.
  - `defeats_cache`: whether this drive can defeat the audio cache
  - `read_offset`: the read offset of the drive

CONTRIBUTING
------------
- Please send pull requests through github.
- You can always [flattr morituri to donate](https://flattr.com/submit/auto?%20%20user_id=thomasvs&url=https://thomas.apestaart.org/morituri/trac/&%20%20title=morituri&%20%20description=morituri&%20%20language=en_GB&tags=flattr,morituri,software&category=software)


