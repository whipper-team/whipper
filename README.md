# Whipper
[![License: GPL v3](https://img.shields.io/badge/License-GPL%20v3-blue.svg)](http://www.gnu.org/licenses/gpl-3.0) [![Current Version](https://img.shields.io/badge/version-0.3.0-green.svg)](https://github.com/JoeLametta/whipper) [![Build Status](https://travis-ci.org/JoeLametta/whipper.svg?branch=master)](https://travis-ci.org/JoeLametta/whipper) [![IRC](https://img.shields.io/badge/chat-on%20freenode-brightgreen.svg)](https://webchat.freenode.net/) [![GitHub Stars](https://img.shields.io/github/stars/JoeLametta/whipper.svg)](https://github.com/JoeLametta/whipper/stargazers) [![GitHub Issues](https://img.shields.io/github/issues/JoeLametta/whipper.svg)](https://github.com/JoeLametta/whipper/issues)

Whipper is a Python 2 CD-DA ripper, fork of the morituri project (_CDDA ripper for *nix systems aiming for accuracy over speed_). It improves morituri which development seems to have halted merging old ignored pull requests, improving it with bugfixes and new features.

In order to track whipper's current development it's advised to check its commit history (README **isn't** complete).

## Table of content
- [Rationale](#rationale)
- [Features](#features)
- [Release history](#release-history)
- [Installation](#installation)
  1. [Required dependencies](#required-dependencies)
  2. [Fetching the source code](#fetching-the-source-code)
  3. [Building the bundled dependencies](#building-the-bundled-dependencies)
  4. [Finalize the installation](#finalize-the-installation)
- [Usage](#usage)
- [Getting started](#getting-started)
- [Configuration file documentation](#configuration-file-documentation)
- [Backward incompatible changes](#backward-incompatible-changes)
- [Running uninstalled](#running-uninstalled)
- [Reporting bugs](#reporting-bugs)
- [License](#license)
- [Contributing](#contributing)
  - [Bug reports & feature requests](#bug-reports--feature-requests)
  - [Developing](#developing)

## Rationale
For a detailed description, see morituri's wiki page: [The Art of the Rip](
https://web.archive.org/web/20160528213242/https://thomas.apestaart.org/thomas/trac/wiki/DAD/Rip).

## Features
* Detects correct sample read offset and ability to defeat cache of drives
* Performs Test & Copy rips
* Verifies rip accuracy using the [AccurateRip database](http://www.accuraterip.com/)
* Uses MusicBrainz for metadata lookup and tagging
* Supports reading the pre-emphasis flag embedded into some CDs and correctly tags the resulting rip
* Detects and rips non digitally silent Hidden Track One Audio
* Provides batch ripping capabilities
* Provides templates for file and directory naming
* Supports lossless encoding
* Allows retagging of already completed rips
* Allows extensibility through external logger plugins

## Release history

- 0.3.0 - Bla bla bla
- 0.2.4 - Bla

## Installation
Whipper isn't currently available in a prepackaged form so, in order to use it, it must be built from its sources.

If you are building from a source tarball or checkout, you can choose to use whipper installed or uninstalled but first install all the required dependencies.

### Required dependencies
Whipper relies on the following packages in order to run correctly and provide all the supported features:
- cdparanoia, for the actual ripping
- cdrdao, for session, TOC, pre-gap, and ISRC extraction
- GStreamer and its python bindings, for encoding (it's going to be removed soon™)
  - gstreamer0.10-base-plugins >= 0.10.22 for appsink
  - gstreamer0.10-good-plugins for wav encoding (it depends on the Linux distro used)
- python musicbrainzngs, for metadata lookup
- python-setuptools, for installation, plugin support
- python-cddb, for showing but not using disc info if not in MusicBrainz
- pycdio, for drive identification
  - Required for drive offset and caching behavior to be stored in the configuration file
- libsndfile, for reading wav files
- flac, for reading flac files
- sox, for track peak detection

### Fetching the source code
  1. Change to a directory where you want to put whipper source code (for example, `$HOME/dev/ext` or `$HOME/prefix/src`)
  2. Clone the repository master branch

    `git clone -b master --single-branch https://github.com/JoeLametta/whipper.git`

  3. Change to its directory

    `cd whipper`

  4. Initialize git submodules

    `git submodule init`

  5. Update the registered submodules

     `git submodule update`

### Building the bundled dependencies
This is only needed if you do not have the `accuraterip-checksum` package installed on your system. Whipper packages this for your convenience:

You can edit the install path in `config.mk`

1. Change to the src directory

   `cd src`

2. Build `accuraterip-checksum`

   `make`

3. Install `accuraterip-checksum`

   `sudo make install`

4. Change to the original directory

   `cd ..`

### Finalize the installation
Install whipper: `python2 setup.py install`

## Usage
Whipper currently only has a command-line interface called `whipper` which is self-documenting: `whipper -h` gives you the basic instructions.

Whipper implements a tree of commands: for example, the top-level `whipper` command has a number of sub-commands.

Positioning of arguments is important:

`whipper cd -d (device) rip`

is correct, while

`whipper cd rip -d (device)`

is not, because the `-d` argument applies to the whipper command.

Check the man page (`whipper(1)`) for more information.

## Getting started
**NEEDS TO BE UPDATED**

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

## Configuration file documentation
The configuration file is stored according to [XDG Base Directory Specification](
http://standards.freedesktop.org/basedir-spec/basedir-spec-latest.html)
when possible.

It lives in `$XDG_CONFIG_HOME/whipper/whipper.conf` (or `$HOME/.config/whipper/whipper.conf`).

The configuration file follows python's ConfigParser syntax.

The possible sections are:

- Main section: [main]
  - `path_filter_fat`: whether to filter path components for FAT file systems
  - `path_filter_special`: whether to filter path components for special characters
- Drive section: [drive:IDENTIFIER], one for each configured drive. All these values are probed by whipper and should not be edited by hand.
  - `defeats_cache`: whether this drive can defeat the audio cache
  - `read_offset`: the read offset of the drive
- Rip command section: [rip.COMMAND.SUBCOMMAND]. Can be used to change the command options default values.

Example section to configure `rip cd rip` defaults:

```
[rip.cd.rip]
unknown = True
output_directory = ~/My Music
track_template = new/%%A/%%y - %%d/%%t - %%n
disc_template = %(track_template)s
profile = flac
```

Note: to get a literal `%` character it must be doubled.

## Backward incompatible changes
* Whipper has adopted new config/cache/state file paths
  * Now always follows XDG specifications
    * Paths used when XDG environment variables are available:
      * `$XDG_CONFIG_HOME/whipper`
      * `$XDG_CACHE_HOME/whipper`
      * `$XDG_DATA_HOME/whipper`
    * Paths used when XDG environment variables are **NOT** available:
      * `$HOME/.config/whipper`
      * `$HOME/.cache/whipper`
      * `$HOME/.local/share/whipper`
  * Configuration file information:
    * `.moriturirc`, `morituri.conf` aren't used anymore
    * When XDG environment variables are available it's located in:
      * `$XDG_CONFIG_HOME/whipper/whipper.conf`
    * When XDG environment variables are **NOT** available it's located in:
      * `$HOME/.config/whipper/whipper.conf`
  * Plugins folder path:
    * When XDG environment variables are available it's located in:
      * `$XDG_DATA_HOME/whipper/plugins`
    * When XDG environment variables are **NOT** available it's located in:
      * `$HOME/.local/share/whipper/plugins`

## Running uninstalled
To make it easier for developers, you can run whipper straight from the
source checkout:

```bash
INSERT UPDATED INSTRUCTIONS HERE
```

## Reporting bugs
whipper's bugs are tracked using the repository issue section provided by GitHub.

When filing bugs, please run the failing command with the environment variable
`RIP_DEBUG` set. For example:

```bash
RIP_DEBUG=5 rip offset find > morituri.log 2>&1
gzip morituri.log
```

And attach the gzipped log file to your bug report.

## License

Copyright (???)

Licensed under the [GNU GPLv3 license](http://www.gnu.org/licenses/gpl-3.0).

## Contributing

### Bug reports & feature requests

Please use the [issue tracker](https://github.com/JoeLametta/whipper/issues) to report any bugs or file feature requests.

### Developing

PRs are welcome.

**INSERT MENTION OF FREENODE #WHIPPER CHANNEL HERE**

**INSERT MENTION OF NON MASTER BRANCHES FORCE PUSH**
