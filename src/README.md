accuraterip-checksum
====================

# Description:
A C99 commandline program to compute the AccurateRip checksum of singletrack WAV files.
Implemented according to

	http://www.hydrogenaudio.org/forums/index.php?showtopic=97603

# Syntax:
	accuraterip-checksum [--version / --accuraterip-v1 / --accuraterip-v2 (default)] filename track_number total_tracks

# Output:
By default, the V2 (AccurateRip version 2) checksum will be printed.
You can also obtain the V1 checksum with the "--accuraterip-v1" parameter.

You can obtain the version of accuraterip-checksum using the "--version" parameter. This is not to be confused with the AccurateRip version!

The version of accuraterip-checksum should be added to audio files which are tagged using the output of accuraterip-checksum. If any severe bugs are ever found in accuraterip-checksum, this will allow you to identify files which were tagged using affected version.


# Compiling:
libsndfile is used for reading the WAV files.
Therefore, on Ubuntu 12.04, make sure you have the following packages installed:

	libsndfile1 (should be installed by default)
	libsndfile1-dev

The configuration files of an Eclipse project are included.
You can use "EGit" (Eclipse git) to import the whole repository.
It should as well ask you to import the project configuration then.

# Author:
Leo Bogert (http://leo.bogert.de)

# Version:
1.4

# Donations:
	bitcoin:14kPd2QWsri3y2irVFX6wC33vv7FqTaEBh

# License:
GPLv3
