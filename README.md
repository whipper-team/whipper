# Whipper

[![license](https://img.shields.io/github/license/JoeLametta/whipper.svg)](https://github.com/JoeLametta/whipper/blob/master/LICENSE)
[![Build Status](https://travis-ci.org/JoeLametta/whipper.svg?branch=master)](https://travis-ci.org/JoeLametta/whipper)
[![GitHub (pre-)release](https://img.shields.io/github/release/joelametta/whipper/all.svg)](https://github.com/JoeLametta/whipper/releases/latest)
[![IRC](https://img.shields.io/badge/irc-%23whipper%40freenode-brightgreen.svg)](https://webchat.freenode.net/?channels=%23whipper)
[![GitHub Stars](https://img.shields.io/github/stars/JoeLametta/whipper.svg)](https://github.com/JoeLametta/whipper/stargazers)
[![GitHub Issues](https://img.shields.io/github/issues/JoeLametta/whipper.svg)](https://github.com/JoeLametta/whipper/issues)
[![GitHub contributors](https://img.shields.io/github/contributors/JoeLametta/whipper.svg)](https://github.com/JoeLametta/whipper/graphs/contributors)

Whipper is a Python 2.7 CD-DA ripper based on the [morituri project](https://github.com/thomasvs/morituri) (_CDDA ripper for *nix systems aiming for accuracy over speed_). It enhances morituri which development seems to have halted merging old ignored pull requests, improving it with bugfixes and new features.

Whipper is currently developed and tested _only_ on Linux distributions but _may_ work fine on other *nix OSes too.

In order to track whipper's latest changes it's advised to check its commit history (README and [CHANGELOG](#changelog) files may not be comprehensive).

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
- [Running uninstalled](#running-uninstalled)
- [Logger plugins](#logger-plugins)
- [License](#license)
- [Contributing](#contributing)
  - [Bug reports & feature requests](#bug-reports--feature-requests)
- [Credits](#credits)
- [Links](#links)

## Rationale

For a detailed description, see morituri's wiki page: [The Art of the Rip](
https://web.archive.org/web/20160528213242/https://thomas.apestaart.org/thomas/trac/wiki/DAD/Rip).

## Features

- Detects correct read offset (in samples)
- Detects whether ripped media is a CD-R
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

Whipper still isn't widely available as an official package in many Linux distributions so, in order to use it, it may be necessary to build it from its source code. If you are building from a source tarball or checkout, you can choose to use whipper installed or uninstalled _but first install all the required dependencies_.

This is a noncomprehensive summary which shows whipper's packaging status (unofficial repositories are probably not included):

[![Packaging status](https://repology.org/badge/vertical-allrepos/whipper.svg)](https://repology.org/metapackage/whipper)

In case you decide to install whipper using an unofficial repository just keep in mind it is your responsibility to verify that the provided content is safe to use.

### Required dependencies

Whipper relies on the following packages in order to run correctly and provide all the supported features:

- [cd-paranoia](https://www.gnu.org/software/libcdio/), for the actual ripping
  - To avoid bugs it's advised to use `cd-paranoia` **10.2+0.94+2-2**
- [cdrdao](http://cdrdao.sourceforge.net/), for session, TOC, pre-gap, and ISRC extraction
- [python-gobject-2](https://packages.debian.org/en/jessie/python-gobject-2), required by `task.py`
- [python-musicbrainzngs](https://github.com/alastair/python-musicbrainzngs), for metadata lookup
- [python-mutagen](https://pypi.python.org/pypi/mutagen), for tagging support
- [python-setuptools](https://pypi.python.org/pypi/setuptools), for installation, plugins support
- [python-cddb](http://cddb-py.sourceforge.net/), for showing (but not using) metadata if disc information aren't available in the MusicBrainz DB
- [python-requests](https://pypi.python.org/pypi/requests), for retrieving AccurateRip database entries
- [pycdio](https://pypi.python.org/pypi/pycdio/), for drive identification (required for drive offset and caching behavior to be stored in the configuration file).
  - To avoid bugs  it's advised to use `pycdio` **0.20** or **0.21** with `libcdio` ≥ **0.90** ≤ **0.94**. If using `libcdio` **0.83**, which is _too old_ to satisfy all the requirements of whipper, just stick to `pycdio` **0.17**. Altough it needs additional testing, `libcdio` **2.0.0** seems to work fine if used with `pycdio` **2.0.0**. All other combinations aren't guaranteed to work.
- [libsndfile](http://www.mega-nerd.com/libsndfile/), for reading wav files
- [flac](https://xiph.org/flac/), for reading flac files
- [sox](http://sox.sourceforge.net/), for track peak detection

### Fetching the source code

Change to a directory where you want to put whipper source code (for example, `$HOME/dev/ext` or `$HOME/prefix/src`)

```bash
git clone https://github.com/JoeLametta/whipper.git
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

Note that, depending on the chosen installation path, this command may require elevated rights.

## Usage

Whipper currently only has a command-line interface called `whipper` which is self-documenting: `whipper -h` gives you the basic instructions.

Whipper implements a tree of commands: for example, the top-level `whipper` command has a number of sub-commands.

Positioning of arguments is important:

`whipper cd -d (device) rip`

is correct, while

`whipper cd rip -d (device)`

is not, because the `-d` argument applies to the `cd` command.

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

The configuration file is stored in `$XDG_CONFIG_HOME/whipper/whipper.conf`, or `$HOME/.config/whipper/whipper.conf` if `$XDG_CONFIG_HOME` is undefined.

See [XDG Base Directory
Specification](http://standards.freedesktop.org/basedir-spec/basedir-spec-latest.html)
and [ConfigParser](https://docs.python.org/2/library/configparser.html).

The configuration file consists of newline-delineated `[sections]`
containing `key = value` pairs. The sections `[main]` and
`[musicbrainz]` are special config sections for options not accessible
from the command line interface.  Sections beginning with `drive` are
written by whipper; certain values should not be edited.

Example configuration demonstrating all `[main]` and `[musicbrainz]`
options:

```INI
[main]
path_filter_fat = True		; replace FAT file system unsafe characters in filenames with _
path_filter_special = False	; replace special characters in filenames with _

[musicbrainz]
server = musicbrainz.org:80	; use MusicBrainz server at host[:port]

[drive:HL-20]
defeats_cache = True		; whether the drive is capable of defeating the audio cache
read_offset = 6			; drive read offset in positive/negative frames (no leading +)
# do not edit the values 'vendor', 'model', and 'release'; they are used by whipper to match the drive

# command line defaults for `whipper cd rip`
[whipper.cd.rip]
unknown = True
output_directory = ~/My Music
track_template = new/%%A/%%y - %%d/%%t - %%n	; note: the format char '%' must be represented '%%'
disc_template = %(track_template)s
# ...
```

## Running uninstalled

To make it easier for developers, you can run whipper straight from the
source checkout:

```bash
python2 -m whipper -h
```

## Logger plugins

Whipper supports using external logger plugins to write rip `.log` files.

List available plugins with `whipper cd rip -h`. Specify a logger to rip with by passing `-L loggername`:

```bash
whipper cd rip -L what
```

### Official logger plugins

Unfortunately both logger plugins are currently outdated and won't work with latest whipper versions.

- [morituri-eaclogger](https://github.com/JoeLametta/morituri-eaclogger) - eac-like logger attempting to maintain strict compatiility with EAC
- [morituri-whatlogger](https://github.com/RecursiveForest/morituri-whatlogger) - eac-like logger containing the informational enhancements of the yamllogger, originally designed for use on What.CD

## License

Licensed under the [GNU GPLv3 license](http://www.gnu.org/licenses/gpl-3.0).

```Text
Copyright (C) 2009 Thomas Vander Stichele
Copyright (C) 2016-2018 the whipper team: JoeLametta, Frederik Olesen,
			Samantha Baldwin, Merlijn Wajer, et al.

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

Make sure you have the latest copy from our [git
repository](https://github.com/JoeLametta/whipper). Where possible,
please include tests for new or changed functionality. You can run tests
with `python -m unittest discover` from your source checkout.

### Bug reports & feature requests

Please use the [issue tracker](https://github.com/JoeLametta/whipper/issues) to report any bugs or to file feature requests.

When filing bug reports, please run the failing command with the environment variable `WHIPPER_DEBUG` set. For example:

```bash
WHIPPER_DEBUG=DEBUG WHIPPER_LOGFILE=whipper.log whipper offset find
gzip whipper.log
```

And attach the gzipped log file to your bug report.

Without `WHIPPER_LOGFILE` set, logging messages will go to stderr. `WHIPPER_DEBUG` accepts a string of the [default python logging levels](https://docs.python.org/2/library/logging.html#logging-levels).

## Credits

Thanks to:

- [Thomas Vander Stichele](https://github.com/thomasvs)
- [Joe Lametta](https://github.com/JoeLametta)
- [Merlijn Wajer](https://github.com/MerlijnWajer)
- [Samantha Baldwin](https://github.com/RecursiveForest)

And to all the [![GitHub contributors](https://img.shields.io/github/contributors/JoeLametta/whipper.svg)](https://github.com/JoeLametta/whipper/graphs/contributors).

## Links

You can find us and talk about the project on IRC: [freenode](https://webchat.freenode.net/?channels=%23whipper), **#whipper** channel.

- [Redacted thread (official)](https://redacted.ch/forums.php?action=viewthread&threadid=150)
- [Repology: versions for whipper](https://repology.org/metapackage/whipper/versions)
- [Unattended ripping using whipper (by Thomas McWork)](https://github.com/thomas-mc-work/most-possible-unattended-rip)
