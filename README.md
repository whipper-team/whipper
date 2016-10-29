# Whipper
[![License: GPL v3](https://img.shields.io/badge/License-GPL%20v3-blue.svg)](http://www.gnu.org/licenses/gpl-3.0) [![Current Version](https://img.shields.io/badge/version-0.3.0-green.svg)](https://github.com/JoeLametta/whipper) [![Build Status](https://travis-ci.org/JoeLametta/whipper.svg?branch=master)](https://travis-ci.org/JoeLametta/whipper) [![IRC](https://img.shields.io/badge/chat-on%20freenode-brightgreen.svg)](https://webchat.freenode.net/?channels=%23whipper) [![GitHub Stars](https://img.shields.io/github/stars/JoeLametta/whipper.svg)](https://github.com/JoeLametta/whipper/stargazers) [![GitHub Issues](https://img.shields.io/github/issues/JoeLametta/whipper.svg)](https://github.com/JoeLametta/whipper/issues)

Whipper is a Python 2 CD-DA ripper, fork of the morituri project (_CDDA ripper for *nix systems aiming for accuracy over speed_). It improves morituri which development seems to have halted merging old ignored pull requests, improving it with bugfixes and new features.

Whipper is developed and tested only on Linux distributions but _should_ work fine on other *nix OSes too.

In order to track whipper's current development it's advised to check its commit history (README **isn't** still complete).

## Table of content
- [Rationale](#rationale)
- [Features](#features)
- [Release history](#release-history)
- [Installation](#installation)
  1. [Required dependencies](#required-dependencies)
  2. [Fetching the source code](#fetching-the-source-code)
  3. [Building the bundled dependencies](#building-the-bundled-dependencies)
  4. [Finalizing the installation](#finalizing-the-installation)
- [Usage](#usage)
- [Getting started](#getting-started)
- [Configuration file documentation](#configuration-file-documentation)
- [Backward incompatible changes](#backward-incompatible-changes)
- [Running uninstalled](#running-uninstalled)
- [License](#license)
- [Contributing](#contributing)
  - [Bug reports & feature requests](#bug-reports--feature-requests)
  - [Developing](#developing)
- [Credits](#credits)
- [Links](#links)

## Rationale
For a detailed description, see morituri's wiki page: [The Art of the Rip](
https://web.archive.org/web/20160528213242/https://thomas.apestaart.org/thomas/trac/wiki/DAD/Rip).

## Features
* Detects correct sample read offset and ability to defeat cache of drives
* Performs Test & Copy rips
* Verifies rip accuracy using the [AccurateRip database](http://www.accuraterip.com/)
* Uses [MusicBrainz](https://musicbrainz.org/doc/About) for metadata lookup
* Supports reading the [pre-emphasis](http://wiki.hydrogenaud.io/index.php?title=Pre-emphasis) flag embedded into some CDs (and correctly tags the resulting rip)
* Detects and rips non digitally silent [Hidden Track One Audio](http://wiki.hydrogenaud.io/index.php?title=HTOA) (HTOA)
* Provides batch ripping capabilities
* Provides templates for file and directory naming
* Supports lossless encoding
* Allows retagging of already completed rips
* Allows extensibility through external logger plugins

## Release history

- 0.3.0 - Bla bla bla
- 0.2.4 - First tagged release after morituri fork

## Installation
With the exception of an [AUR package for Arch Linux](https://aur.archlinux.org/packages/whipper-git), whipper isn't currently available in a prepackaged form so, in order to use it, it must be built from its source code.

If you are building from a source tarball or checkout, you can choose to use whipper installed or uninstalled _but first install all the required dependencies_.

### Required dependencies
Whipper relies on the following packages in order to run correctly and provide all the supported features:
- cdparanoia, for the actual ripping
- cdrdao, for session, TOC, pre-gap, and ISRC extraction
- GStreamer and its python bindings, for encoding (it's going to be removed soon™)
  - gstreamer0.10-base-plugins >= 0.10.22 for appsink
  - gstreamer0.10-good-plugins for wav encoding (it depends on the Linux distro used)
- python-musicbrainzngs, for metadata lookup
- python-setuptools, for installation, plugins support
- python-cddb, for showing but not using metadata if disc not available in the MusicBrainz DB
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

  4. Initialize the git submodules

    `git submodule init`

  5. Update the registered submodules

     `git submodule update`

### Building the bundled dependencies
This is only needed if you do not have the `accuraterip-checksum` package installed on your system. Whipper packages this for your convenience:

You can edit the install path in `config.mk`

1. Change to the src directory

   `cd src`

2. Compile `accuraterip-checksum`

   `make`

3. Install `accuraterip-checksum`

   `sudo make install`

4. Change to the original directory

   `cd ..`

### Finalizing the installation
Install whipper: `python2 setup.py install`

## Usage
Whipper currently only has a command-line interface called `whipper` which is self-documenting: `whipper -h` gives you the basic instructions.

Whipper implements a tree of commands: for example, the top-level `whipper` command has a number of sub-commands.

Positioning of arguments is important:

`whipper cd -d (device) rip`

is correct, while

`whipper cd rip -d (device)`

is not, because the `-d` argument applies to the whipper command.

~~Check the man page (`whipper(1)`) for more information.~~ (currently not available)

## Getting started
The simplest way to get started making accurate rips is:

1. Pick a relatively popular CD that has a good change of being in the AccurateRip database
2. Analyze the drive's caching behavior

   `whipper drive analyze`

3. Find the drive's offset by running

   - `whipper offset find`

   - Wait for it to complete; this might take a while. Optionally, confirm this offset with two more discs.

   - If this step fails, please look below.

   Unfortunately the current `offset find` feature is quite unreliable and can easily fail; if that happens you can find the correct offset for your drive in this way:

   1. Find the drive's model number

      `whipper drive list`

   2. Head to [AccurateRip's CD Drive Offset webpage](http://www.accuraterip.com/driveoffsets.htm)
   3. Search the table for the model you previously found
      - If nothing matches, try to refine your search
   4. Open in a text editor the file located at: `$HOME/.config/whipper/whipper.conf`
   5. Append the following text line to the bottom of the file replacing `value_here` with:
      - The unsigned offset value (if positive)
      - The signed offset value (if negative)

      `read_offset = value_here` (example: `read_offset = 6`)
   6. Mission accomplished :)

4. Rip the disc by running

   `whipper cd rip` (uses the offset from the configuration file)

   or

   `whipper cd rip --offset (the number you got before)` (manually specified offset)

## Configuration file documentation
The configuration file is stored according to the [XDG Base Directory Specification](
http://standards.freedesktop.org/basedir-spec/basedir-spec-latest.html)
when possible.

It lives in `$XDG_CONFIG_HOME/whipper/whipper.conf` (or `$HOME/.config/whipper/whipper.conf`).

The configuration file follows python's [ConfigParser](https://docs.python.org/2/library/configparser.html) syntax.

The possible sections are:

- Main section: `[main]`
  - `path_filter_fat`: whether to filter path components for FAT file systems
  - `path_filter_special`: whether to filter path components for special characters

- Drive section: `[drive:IDENTIFIER]`, one for each configured drive. All these values are probed by whipper and should not be edited by hand.
  - `defeats_cache`: whether this drive can defeat the audio cache
  - `read_offset`: the read offset of the drive

- Rip command section: `[rip.COMMAND.SUBCOMMAND]`. Can be used to change the command options default values.

Example section to configure `whipper cd rip` defaults:

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
_**NEEDS TO BE UPDATED**_

To make it easier for developers, you can run whipper straight from the
source checkout:

```bash
INSERT UPDATED INSTRUCTIONS HERE
```

## License

Copyright (???)

Licensed under the [GNU GPLv3 license](http://www.gnu.org/licenses/gpl-3.0).

## Contributing

### Bug reports & feature requests

Please use the [issue tracker](https://github.com/JoeLametta/whipper/issues) to report any bugs or file feature requests.

When filing bug reports, please run the failing command with the environment variable `RIP_DEBUG` set. For example:

```bash
RIP_DEBUG=5 whipper offset find > whipper.log 2>&1
gzip whipper.log
```

And attach the gzipped log file to your bug report.

### Developing

Pull requests are welcome.

**WARNING:** As whipper is still under heavy development sometimes I will force push (`--force-with-lease`) to the non master branches.

## Credits

Thanks to ...

- aaa (qwe)
- bbb (rty)
- ccc (uio)

## Links
You can find us and talk about the project on IRC: [freenode](https://webchat.freenode.net/?channels=%23whipper), **#whipper** channel.

- [What.CD thread (official)](https://what.cd/forums.php?action=viewthread&threadid=163034)
- [Reddit thread (unofficial)](https://www.reddit.com/r/linux/comments/53hyw1/github_joelamettawhipper_for_those_about_to_rip_a/)
- [Arch Linux whipper AUR package](https://aur.archlinux.org/packages/whipper-git/)
