# Whipper

[![license](https://img.shields.io/github/license/JoeLametta/whipper.svg)](https://github.com/JoeLametta/whipper/blob/master/LICENSE) [![Build Status](https://travis-ci.org/JoeLametta/whipper.svg?branch=master)](https://travis-ci.org/JoeLametta/whipper) [![GitHub (pre-)release](https://img.shields.io/github/release/joelametta/whipper/all.svg)](https://github.com/JoeLametta/whipper/releases/latest) [![IRC](https://img.shields.io/badge/irc-%23whipper%40freenode-brightgreen.svg)](https://webchat.freenode.net/?channels=%23whipper) [![GitHub Stars](https://img.shields.io/github/stars/JoeLametta/whipper.svg)](https://github.com/JoeLametta/whipper/stargazers) [![GitHub Issues](https://img.shields.io/github/issues/JoeLametta/whipper.svg)](https://github.com/JoeLametta/whipper/issues) [![GitHub contributors](https://img.shields.io/github/contributors/JoeLametta/whipper.svg)](https://github.com/JoeLametta/whipper/graphs/contributors)

Whipper is a Python 2.7 CD-DA ripper, fork of the morituri project (_CDDA ripper for *nix systems aiming for accuracy over speed_). It improves morituri which development seems to have halted merging old ignored pull requests, improving it with bugfixes and new features.

Whipper is developed and tested _only_ on Linux distributions but _may_ work fine on other *nix OSes too.

In order to track whipper's current development it's advised to check its commit history (README **isn't** still complete).

## Table of content

- [Rationale](#rationale)
- [Features](#features)
- [Changelog](#changelog)
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
- [Logger plugins](#logger-plugins)
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

- Detects correct read offset (in samples)
- Has ability to defeat cache of drives
- Performs Test & Copy rips
- Verifies rip accuracy using the [AccurateRip database](http://www.accuraterip.com/)
- Uses [MusicBrainz](https://musicbrainz.org/doc/About) for metadata lookup
- Supports reading the [pre-emphasis](http://wiki.hydrogenaud.io/index.php?title=Pre-emphasis) flag embedded into some CDs (and correctly tags the resulting rip)
- Detects and rips _non digitally silent_ [Hidden Track One Audio](http://wiki.hydrogenaud.io/index.php?title=HTOA) (HTOA)
- Provides batch ripping capabilities
- Provides templates for file and directory naming
- Supports lossless encoding of ripped audio tracks (FLAC)
- Allows extensibility through external logger plugins

## Changelog

See [CHANGELOG.md](https://github.com/JoeLametta/whipper/blob/master/CHANGELOG.md).

For detailed information, please check the commit history.

## Installation

With the exception of an [Arch Linux package](https://www.archlinux.org/packages/community/any/whipper/) and a [Copr repository for Fedora](https://copr.fedorainfracloud.org/coprs/mruszczyk/whipper/), whipper isn't currently available in a prepackaged form so, in order to use it, it must be built from its source code.

If you are building from a source tarball or checkout, you can choose to use whipper installed or uninstalled _but first install all the required dependencies_.

### Required dependencies

Whipper relies on the following packages in order to run correctly and provide all the supported features:

- [cdparanoia](https://www.xiph.org/paranoia/), for the actual ripping
- [cdrdao](http://cdrdao.sourceforge.net/), for session, TOC, pre-gap, and ISRC extraction
- [python-gobject-2](https://packages.debian.org/en/jessie/python-gobject-2), required by `task.py`
- [python-musicbrainzngs](https://github.com/alastair/python-musicbrainzngs), for metadata lookup
- [python-mutagen](https://pypi.python.org/pypi/mutagen), for tagging support
- [python-setuptools](https://pypi.python.org/pypi/setuptools), for installation, plugins support
- [pycdio](https://pypi.python.org/pypi/pycdio/) (to avoid bugs please use `pycdio` **0.20** & `libcdio` >= **0.90** or, with previous `libcdio` versions, `pycdio` **0.17**), for drive identification
  - Required for drive offset and caching behavior to be stored in the configuration file
- [requests](https://pypi.python.org/pypi/requests) for retrieving AccurateRip database entries
- [libsndfile](http://www.mega-nerd.com/libsndfile/), for reading wav files
- [flac](https://xiph.org/flac/), for reading flac files
- [sox](http://sox.sourceforge.net/), for track peak detection

### Fetching the source code

Change to a directory where you want to put whipper source code (for example, `$HOME/dev/ext` or `$HOME/prefix/src`)

```bash
git clone -b master --single-branch https://github.com/JoeLametta/whipper.git
cd whipper
```

### Building the bundled dependencies

Whipper uses and packages a slightly different version of the `accuraterip-checksum` tool:

You can edit the install path in `config.mk`

```bash
cd src
make
sudo make install
cd ..
```

### Finalizing the installation

Install whipper: `python2 setup.py install`

## Usage

Whipper currently only has a command-line interface called `whipper` which is self-documenting: `whipper -h` gives you the basic instructions.

Whipper implements a tree of commands: for example, the top-level `whipper` command has a number of sub-commands.

Positioning of arguments is important:

`whipper cd -d (device) rip`

is correct, while

`whipper cd rip -d (device)`

is not, because the `-d` argument applies to the `cd` command.

~~Check the man page (`whipper(1)`) for more information.~~ (currently not available as whipper's documentation is planned to be reworked ([Issue #73](https://github.com/JoeLametta/whipper/issues/73))).

## Getting started

The simplest way to get started making accurate rips is:

1. Pick a relatively popular CD that has a good chance of being in the AccurateRip database
2. Analyze the drive's caching behavior

   `whipper drive analyze`

3. Find the drive's offset.

   Consult the [AccurateRip's CD Drive Offset database](http://www.accuraterip.com/driveoffsets.htm) for your drive. Drive information can be retrieved with `whipper drive list`.

   `whipper offset find -o insert-numeric-value-here`

   If you omit the `-o` argument, whipper will try a long, popularity-sorted list of drive offsets.

   If you can not confirm your drive offset value but wish to set a default regardless, set `read_offset = insert-numeric-value-here` in `whipper.conf`.

   Offsets confirmed with `whipper offset find` are automatically written to the configuration file.

   If specifying the offset manually, please note that: if positive it must be written as a number without sign (ex: `+102` -> `102`), if negative it must include the sign too (ex: `-102` -> `-102`).

4. Rip the disc by running

   `whipper cd rip`

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
  **Please note that this feature is currently broken (being this way since [PR #122](https://github.com/JoeLametta/whipper/pull/92) / whipper v0.4.1).**

Example section to configure `whipper cd rip` defaults:

```Python
[rip.cd.rip]
unknown = True
output_directory = ~/My Music
track_template = new/%%A/%%y - %%d/%%t - %%n
disc_template = %(track_template)s
profile = flac
```

Note: to get a literal `%` character it must be doubled.

## Backward incompatible changes

- Profiles (for encoding) aren't supported anymore since ([PR #121](https://github.com/JoeLametta/whipper/pull/121) / whipper v0.5.0): now whipper encodes to FLAC
- The image retag feature has been knowingly broken since ([PR #130](https://github.com/JoeLametta/whipper/pull/130))
- Structural changes broke compatibility with existing logger plugins ([PR #94](https://github.com/JoeLametta/whipper/pull/94))
- Dropped external git submodules ([PR #31](https://github.com/JoeLametta/whipper/pull/31), [PR #92](https://github.com/JoeLametta/whipper/pull/92))
- Whipper executable name changed: from `rip` to `whipper` ([PR #70](https://github.com/JoeLametta/whipper/pull/70))
- Whipper has adopted new config/cache/state file paths ([PR #42](https://github.com/JoeLametta/whipper/pull/42))
  - Now always follows XDG specifications

    - Paths used when XDG environment variables are available:
      - `$XDG_CONFIG_HOME/whipper`
      - `$XDG_CACHE_HOME/whipper`
      - `$XDG_DATA_HOME/whipper`

    - Paths used when XDG environment variables are **NOT** available:
      - `$HOME/.config/whipper`
      - `$HOME/.cache/whipper`
      - `$HOME/.local/share/whipper`

  - Configuration file information:
    - `.moriturirc`, `morituri.conf` aren't used anymore

    - When XDG environment variables are available it's located in:
      - `$XDG_CONFIG_HOME/whipper/whipper.conf`

    - When XDG environment variables are **NOT** available it's located in:
      - `$HOME/.config/whipper/whipper.conf`

  - Plugins folder path:
    - When XDG environment variables are available it's located in:
      - `$XDG_DATA_HOME/whipper/plugins`

    - When XDG environment variables are **NOT** available it's located in:
      - `$HOME/.local/share/whipper/plugins`

## Running uninstalled

To make it easier for developers, you can run whipper straight from the
source checkout:

```bash
python2 setup.py develop --user
whipper -h
```

## Logger plugins

Whipper supports using external logger plugins to write rip `.log` files.

List available plugins with `whipper cd rip -h`. Specify a logger to rip with by passing `-L loggername`:

```bash
whipper cd rip -L what
```

### Official loggers

- [morituri-yamlloger](https://github.com/JoeLametta/morituri-yamllogger) - default whipper logger (provided as external logger for compatibility with morituri), yaml format
- [morituri-eaclogger](https://github.com/JoeLametta/morituri-eaclogger) - eac-like logger attempting to maintain strict compatiility with EAC
- [morituri-whatlogger](https://github.com/RecursiveForest/morituri-whatlogger) - eac-like logger containing the informational enhancements of the yamllogger, originally designed for use on What.CD

## License

Licensed under the [GNU GPLv3 license](http://www.gnu.org/licenses/gpl-3.0).

```Text
Copyright (C) 2009 Thomas Vander Stichele
Copyright (C) 2016, 2017 JoeLametta

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software Foundation,
Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301  USA
```

## Contributing

### Bug reports & feature requests

Please use the [issue tracker](https://github.com/JoeLametta/whipper/issues) to report any bugs or to file feature requests.

When filing bug reports, please run the failing command with the environment variable `WHIPPER_DEBUG` set. For example:

```bash
WHIPPER_DEBUG=DEBUG WHIPPER_LOGFILE=whipper.log whipper offset find
gzip whipper.log
```

And attach the gzipped log file to your bug report.

Without `WHIPPER_LOGFILE` set, logging messages will go to stderr. `WHIPPER_DEBUG` accepts a string of the [default python logging levels](https://docs.python.org/2/library/logging.html#logging-levels).

### Developing

Pull requests are welcome.

**WARNING:** As whipper is still under heavy development sometimes I will force push (`--force-with-lease`) to the non master branches.

## Credits

Thanks to:

- [Thomas Vander Stichele](https://github.com/thomasvs)
- [Joe Lametta](https://github.com/JoeLametta)
- [Merlijn Wajer](https://github.com/MerlijnWajer)
- [Samantha Baldwin](https://github.com/RecursiveForest)

## Links

You can find us and talk about the project on IRC: [freenode](https://webchat.freenode.net/?channels=%23whipper), **#whipper** channel.

- [Redacted thread (official)](https://redacted.ch/forums.php?action=viewthread&threadid=150)
- [Arch Linux package](https://www.archlinux.org/packages/community/any/whipper/)
- [Arch Linux whipper-git AUR package](https://aur.archlinux.org/packages/whipper-git/)
- [Fedora Copr repository for whipper](https://copr.fedorainfracloud.org/coprs/mruszczyk/whipper/)
- [Unattended ripping using whipper (script by Thomas McWork)](https://github.com/thomas-mc-work/most-possible-unattended-rip)
