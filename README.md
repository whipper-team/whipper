# Whipper

[![license](https://img.shields.io/github/license/whipper-team/whipper.svg)](https://github.com/whipper-team/whipper/blob/master/LICENSE)
[![Build Status](https://travis-ci.com/whipper-team/whipper.svg?branch=master)](https://travis-ci.com/whipper-team/whipper)
[![GitHub (pre-)release](https://img.shields.io/github/release/whipper-team/whipper/all.svg)](https://github.com/whipper-team/whipper/releases/latest)
[![IRC](https://img.shields.io/badge/irc-%23whipper%40freenode-brightgreen.svg)](https://webchat.freenode.net/?channels=%23whipper)
[![GitHub Stars](https://img.shields.io/github/stars/whipper-team/whipper.svg)](https://github.com/whipper-team/whipper/stargazers)
[![GitHub Issues](https://img.shields.io/github/issues/whipper-team/whipper.svg)](https://github.com/whipper-team/whipper/issues)
[![GitHub contributors](https://img.shields.io/github/contributors/whipper-team/whipper.svg)](https://github.com/whipper-team/whipper/graphs/contributors)

Whipper is a Python 2.7 CD-DA ripper based on the [morituri project](https://github.com/thomasvs/morituri) (_CDDA ripper for *nix systems aiming for accuracy over speed_). It enhances morituri which development seems to have halted merging old ignored pull requests, improving it with bugfixes and new features.

Whipper is currently developed and tested _only_ on Linux distributions but _may_ work fine on other *nix OSes too.

In order to track whipper's latest changes it's advised to check its commit history (README and [CHANGELOG](#changelog) files may not be comprehensive).

## Table of content

- [Rationale](#rationale)
- [Features](#features)
- [Changelog](#changelog)
- [Installation](#installation)
  * [Docker](#docker)
  * [Package](#package)
- [Building](#building)
  1. [Required dependencies](#required-dependencies)
  2. [Fetching the source code](#fetching-the-source-code)
  3. [Building the bundled dependencies](#building-the-bundled-dependencies)
  4. [Finalizing the build](#finalizing-the-build)
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
- Supports reading the [pre-emphasis](http://wiki.hydrogenaud.io/index.php?title=Pre-emphasis) flag embedded into some CDs (and correctly tags the resulting rip). _Currently whipper only reports the pre-emphasis flag value stored in the TOC._
- Detects and rips _non digitally silent_ [Hidden Track One Audio](http://wiki.hydrogenaud.io/index.php?title=HTOA) (HTOA)
- Provides batch ripping capabilities
- Provides templates for file and directory naming
- Supports lossless encoding of ripped audio tracks (FLAC)
- Allows extensibility through external logger plugins

## Changelog

See [CHANGELOG.md](https://github.com/whipper-team/whipper/blob/master/CHANGELOG.md).

For detailed information, please check the commit history.

## Installation

Whipper still isn't available as an official package in every Linux distributions so, in order to use it, it may be necessary to [build it from its source code](#building).

### Docker

You can easily install whipper without needing to care about the required dependencies by making use of the automatically built images hosted on Docker Hub:

`docker pull joelametta/whipper`

Alternatively, in case you prefer building Docker images locally, just issue the following command (it relies on the [Dockerfile](https://github.com/whipper-team/whipper/blob/master/Dockerfile) included in whipper's repository):

`docker build -t whipper/whipper`

It's recommended to create an alias for a convenient usage:

```bash
alias whipper="docker run -ti --rm --device=/dev/cdrom \
    -v ~/.config/whipper:/home/worker/.config/whipper \
    -v ${PWD}/output:/output \
    whipper/whipper"
```

You should put this e.g. into your `.bash_aliases`. Also keep in mind to substitute the path definitions to something that fits to your needs (e.g. replace `… -v ${PWD}/output:/output …` with `… -v ${HOME}/ripped:/output \ …`).

Make sure you create the configuration directory:

`mkdir -p ~/.config/whipper ${PWD}/output`

Finally you can test the correct installation:

```
whipper -v
whipper drive list
```

### Package

This is a noncomprehensive summary which shows whipper's packaging status (unofficial repositories are probably not included):

[![Packaging status](https://repology.org/badge/vertical-allrepos/whipper.svg)](https://repology.org/metapackage/whipper)

In case you decide to install whipper using an unofficial repository just keep in mind it is your responsibility to verify that the provided content is safe to use.

## Building

If you are building from a source tarball or checkout, you can choose to use whipper installed or uninstalled _but first install all the required dependencies_.

### Required dependencies

Whipper relies on the following packages in order to run correctly and provide all the supported features:

- [cd-paranoia](https://www.gnu.org/software/libcdio/), for the actual ripping
  - To avoid bugs it's advised to use `cd-paranoia` version **10.2+0.94+2-2**
  - The package named `libcdio-utils`, available on Debian and Ubuntu, is affected by a bug: it doesn't include the `cd-paranoia` binary (needed by whipper). For more details see: [#888053 (Debian)](https://bugs.debian.org/cgi-bin/bugreport.cgi?bug=888053), [#1750264 (Ubuntu)](https://bugs.launchpad.net/ubuntu/+source/libcdio/+bug/1750264).
- [cdrdao](http://cdrdao.sourceforge.net/), for session, TOC, pre-gap, and ISRC extraction
- [GObject Introspection](https://wiki.gnome.org/Projects/GObjectIntrospection), to provide GLib-2.0 methods used by `task.py`
- [PyGObject](https://pypi.org/project/PyGObject/), required by `task.py`
- [python-musicbrainzngs](https://github.com/alastair/python-musicbrainzngs), for metadata lookup
- [python-mutagen](https://pypi.python.org/pypi/mutagen), for tagging support
- [python-setuptools](https://pypi.python.org/pypi/setuptools), for installation, plugins support
- [python-requests](https://pypi.python.org/pypi/requests), for retrieving AccurateRip database entries
- [pycdio](https://pypi.python.org/pypi/pycdio/), for drive identification (required for drive offset and caching behavior to be stored in the configuration file).
  - To avoid bugs  it's advised to use `pycdio` **0.20** or **0.21** with `libcdio` ≥ **0.90** ≤ **0.94* or `pycdio` **2.0.0** with `libcdio` **2.0.0**. All other combinations won't probably work.
- [libsndfile](http://www.mega-nerd.com/libsndfile/), for reading wav files
- [flac](https://xiph.org/flac/), for reading flac files
- [sox](http://sox.sourceforge.net/), for track peak detection

Some dependencies aren't available in the PyPI. They can be probably installed using your distribution's package manager:

- [cd-paranoia](https://www.gnu.org/software/libcdio/)
- [cdrdao](http://cdrdao.sourceforge.net/)
- [GObject Introspection](https://wiki.gnome.org/Projects/GObjectIntrospection)
- [libsndfile](http://www.mega-nerd.com/libsndfile/)
- [flac](https://xiph.org/flac/)
- [sox](http://sox.sourceforge.net/)

PyPI installable dependencies are listed in the [requirements.txt](https://github.com/whipper-team/whipper/blob/master/requirements.txt) file and can be installed issuing the following command:

`pip install -r requirements.txt`

### Fetching the source code

Change to a directory where you want to put whipper source code (for example, `$HOME/dev/ext` or `$HOME/prefix/src`)

```bash
git clone https://github.com/whipper-team/whipper.git
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

### Finalizing the build

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
disc_template =  new/%%A/%%y - %%d/%%A - %%d
# ...
```

## Running uninstalled

To make it easier for developers, you can run whipper straight from the
source checkout:

```bash
python2 -m whipper -h
```

## Logger plugins

Whipper allows using external logger plugins to customize the template of `.log` files.

The available plugins can be listed with `whipper cd rip -h`. Specify a logger to rip with by passing `-L loggername`:

```bash
whipper cd rip -L eac
```

Whipper searches for logger plugins in the following paths:

- `$XDG_DATA_HOME/whipper/plugins`
- Paths returned by the following Python instruction:

  `[x + '/whipper/plugins' for x in site.getsitepackages()]`

- If whipper is run in a `virtualenv`, it will use these alternative instructions (from `distutils.sysconfig`):
  - `get_python_lib(plat_specific=False, standard_lib=False, prefix='/usr/local') + '/whipper/plugins'`
  - `get_python_lib(plat_specific=False, standard_lib=False) + '/whipper/plugins'`

On a default Debian/Ubuntu installation, the following paths are searched by whipper:

- `$HOME/.local/share/whipper/plugins`
- `/usr/local/lib/python2.7/dist-packages/whipper/plugins`
- `/usr/lib/python2.7/dist-packages/whipper/plugins`

### Official logger plugins

I suggest using whipper's default logger unless you've got particular requirements.

- [whipper-plugin-eaclogger](https://github.com/whipper-team/whipper-plugin-eaclogger) - a plugin for whipper which provides EAC style log reports

## License

Licensed under the [GNU GPLv3 license](http://www.gnu.org/licenses/gpl-3.0).

```Text
Copyright (C) 2009 Thomas Vander Stichele
Copyright (C) 2016-2018 The Whipper Team: JoeLametta, Frederik Olesen,
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
repository](https://github.com/whipper-team/whipper). Where possible,
please include tests for new or changed functionality. You can run tests
with `python -m unittest discover` from your source checkout.

### Bug reports & feature requests

Please use the [issue tracker](https://github.com/whipper-team/whipper/issues) to report any bugs or to file feature requests.

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

And to all the [contributors](https://github.com/whipper-team/whipper/graphs/contributors).

## Links

You can find us and talk about the project on:

- IRC: [freenode](https://webchat.freenode.net/?channels=%23whipper), **#whipper** channel
- Matrix (the room is a bridge to freenode IRC)
  - Access Matrix  through the [Riot.im web client](https://riot.im/app/#/room/!wxdgcGzudITUpZMCrn:matrix.org)
  - Join to the room named `#freenode_#whipper:matrix.org`
- [Redacted thread (official)](https://redacted.ch/forums.php?action=viewthread&threadid=150)

Other relevant links:
- [Repology: versions for whipper](https://repology.org/metapackage/whipper/versions)
- [Unattended ripping using whipper (by Thomas McWork)](https://github.com/thomas-mc-work/most-possible-unattended-rip)
