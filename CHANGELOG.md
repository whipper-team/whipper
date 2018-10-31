# Change Log

## [Unreleased](https://github.com/whipper-team/whipper/tree/HEAD)

[Full Changelog](https://github.com/whipper-team/whipper/compare/v0.7.2...HEAD)

## [v0.7.2](https://github.com/whipper-team/whipper/tree/v0.7.2) (2018-10-31)
[Full Changelog](https://github.com/whipper-team/whipper/compare/v0.7.1...v0.7.2)

**Implemented enhancements:**

- Add whipper to Hydrogen Audio wiki's "Comparison of CD rippers" [\#317](https://github.com/whipper-team/whipper/issues/317)
- automatically build Docker images [\#301](https://github.com/whipper-team/whipper/issues/301)

**Fixed bugs:**

- UnicodeEncodeError: 'ascii' codec can't encode characters in position 17-18: ordinal not in range\(128\) [\#315](https://github.com/whipper-team/whipper/issues/315)

**Closed issues:**

- Make 0.7.1 release \(before GCI 😅\) [\#312](https://github.com/whipper-team/whipper/issues/312)

**Merged pull requests:**

- Explicitly encode path as UTF-8 in truncate\_filename\(\) [\#319](https://github.com/whipper-team/whipper/pull/319) ([Freso](https://github.com/Freso))
- Add AppStream metainfo.xml file [\#318](https://github.com/whipper-team/whipper/pull/318) ([Freso](https://github.com/Freso))

## [v0.7.1](https://github.com/whipper-team/whipper/tree/v0.7.1) (2018-10-23)
[Full Changelog](https://github.com/whipper-team/whipper/compare/v0.7.0...v0.7.1)

**Implemented enhancements:**

- Transfer repository ownership to GitHub organization [\#306](https://github.com/whipper-team/whipper/issues/306)
- Add cdparanoia version to log file [\#267](https://github.com/whipper-team/whipper/issues/267)
- Remove whipper's retag feature [\#262](https://github.com/whipper-team/whipper/issues/262)
- Add a requirements.txt file [\#221](https://github.com/whipper-team/whipper/issues/221)
- Limit length of filenames [\#197](https://github.com/whipper-team/whipper/issues/197)
- Loggers [\#117](https://github.com/whipper-team/whipper/issues/117)

**Fixed bugs:**

- TypeError on whipper offset find [\#263](https://github.com/whipper-team/whipper/issues/263)
- Catch DNS error [\#206](https://github.com/whipper-team/whipper/issues/206)

**Closed issues:**

- Disable eject button when ripping [\#308](https://github.com/whipper-team/whipper/issues/308)
- Github repo [\#293](https://github.com/whipper-team/whipper/issues/293)

**Merged pull requests:**

- Limit length of filenames [\#311](https://github.com/whipper-team/whipper/pull/311) ([JoeLametta](https://github.com/JoeLametta))
- Add a requirements.txt file [\#310](https://github.com/whipper-team/whipper/pull/310) ([JoeLametta](https://github.com/JoeLametta))
- Reorder Dockerfile for performance [\#305](https://github.com/whipper-team/whipper/pull/305) ([anarcat](https://github.com/anarcat))
- Handle FreeDB server errors gracefully  [\#304](https://github.com/whipper-team/whipper/pull/304) ([anarcat](https://github.com/anarcat))
- Fix Docker invocation [\#300](https://github.com/whipper-team/whipper/pull/300) ([anarcat](https://github.com/anarcat))
- Document Docker usage in the README [\#297](https://github.com/whipper-team/whipper/pull/297) ([thomas-mc-work](https://github.com/thomas-mc-work))
- switch CDDB implementation to freedb.py from python-audio-tools [\#276](https://github.com/whipper-team/whipper/pull/276) ([mtdcr](https://github.com/mtdcr))
- task: implement logging [\#272](https://github.com/whipper-team/whipper/pull/272) ([mtdcr](https://github.com/mtdcr))
- Switch to PyGObject by default [\#271](https://github.com/whipper-team/whipper/pull/271) ([mtdcr](https://github.com/mtdcr))
- Remove whipper's image retag feature [\#269](https://github.com/whipper-team/whipper/pull/269) ([JoeLametta](https://github.com/JoeLametta))
- Incremental code modernization for \(future\) Python 3 port [\#268](https://github.com/whipper-team/whipper/pull/268) ([JoeLametta](https://github.com/JoeLametta))
- Remove dead code from program.getFastToc [\#264](https://github.com/whipper-team/whipper/pull/264) ([mtdcr](https://github.com/mtdcr))
- Add Dockerfile [\#237](https://github.com/whipper-team/whipper/pull/237) ([thomas-mc-work](https://github.com/thomas-mc-work))

## [v0.7.0](https://github.com/whipper-team/whipper/tree/v0.7.0) (2018-04-09)
[Full Changelog](https://github.com/whipper-team/whipper/compare/v0.6.0...v0.7.0)

**Implemented enhancements:**

- Various ripping issues [\#179](https://github.com/whipper-team/whipper/issues/179)
- Simple message while reading TOC [\#257](https://github.com/whipper-team/whipper/issues/257)
- Small readme cleanups [\#250](https://github.com/whipper-team/whipper/pull/250) ([RecursiveForest](https://github.com/RecursiveForest))
- Remove debug commands, add mblookup command [\#249](https://github.com/whipper-team/whipper/pull/249) ([RecursiveForest](https://github.com/RecursiveForest))
- remove -T/--toc-pickle [\#245](https://github.com/whipper-team/whipper/pull/245) ([RecursiveForest](https://github.com/RecursiveForest))
- credit four major developers by line count [\#243](https://github.com/whipper-team/whipper/pull/243) ([RecursiveForest](https://github.com/RecursiveForest))
- Removed reference to unused "profile = flac" config option \(issue \#99\) [\#231](https://github.com/whipper-team/whipper/pull/231) ([calumchisholm](https://github.com/calumchisholm))

**Fixed bugs:**

- whipper offset find exception [\#208](https://github.com/whipper-team/whipper/issues/208)
- cd rip   is not able to rip the last track [\#203](https://github.com/whipper-team/whipper/issues/203)
- whipper not picking up all settings in whipper.conf [\#99](https://github.com/whipper-team/whipper/issues/99)
- ImportError: libcdio.so.16: cannot open shared object file: No such file or directory [\#229](https://github.com/whipper-team/whipper/issues/229)
- fix CI build error with latest pycdio [\#233](https://github.com/whipper-team/whipper/pull/233) ([thomas-mc-work](https://github.com/thomas-mc-work))

**Closed issues:**

- Make a 0.6.0 release [\#219](https://github.com/whipper-team/whipper/issues/219)
- CD-ROM powers off during rip command. [\#189](https://github.com/whipper-team/whipper/issues/189)
- Remove connection to parent fork. [\#79](https://github.com/whipper-team/whipper/issues/79)
- GUI frontend for whipper [\#40](https://github.com/whipper-team/whipper/issues/40)

**Merged pull requests:**

- Remove reference to Copr repository [\#248](https://github.com/whipper-team/whipper/pull/248) ([mruszczyk](https://github.com/mruszczyk))
- Revert "Convert docstrings to reStructuredText" [\#246](https://github.com/whipper-team/whipper/pull/246) ([RecursiveForest](https://github.com/RecursiveForest))
- remove radon reports [\#242](https://github.com/whipper-team/whipper/pull/242) ([RecursiveForest](https://github.com/RecursiveForest))
- read command parameters from config sections [\#240](https://github.com/whipper-team/whipper/pull/240) ([RecursiveForest](https://github.com/RecursiveForest))

## [v0.6.0](https://github.com/whipper-team/whipper/tree/v0.6.0) (2018-02-02)
[Full Changelog](https://github.com/whipper-team/whipper/compare/v0.5.1...v0.6.0)

**Implemented enhancements:**

- Error: NotFoundException message displayed while ripping an unknown disc [\#198](https://github.com/whipper-team/whipper/issues/198)
- rename milestone 101010 to backlog [\#190](https://github.com/whipper-team/whipper/issues/190)
- Use 'Artist as credited' in filename instead of 'Artist in MusicBrainz' \(e.g. to solve \[unknown\]\) [\#155](https://github.com/whipper-team/whipper/issues/155)
- Declare supported Python version [\#152](https://github.com/whipper-team/whipper/issues/152)
- Update doc/release or remove it [\#149](https://github.com/whipper-team/whipper/issues/149)
- Test HTOA peak value against 0 \(integer equality\) [\#143](https://github.com/whipper-team/whipper/issues/143)
- Identify media type in log file \(ie CD vs CD-R\) [\#137](https://github.com/whipper-team/whipper/issues/137)
- Rename the Python module [\#100](https://github.com/whipper-team/whipper/issues/100)
- libcdio-paranoia instead of cdparanoia [\#87](https://github.com/whipper-team/whipper/issues/87)
- Support both AccurateRip V1 and AccurateRip V2 at the same time [\#18](https://github.com/whipper-team/whipper/issues/18)
- Test HTOA peak value against 0 \(integer comparison\) [\#224](https://github.com/whipper-team/whipper/pull/224) ([JoeLametta](https://github.com/JoeLametta))

**Fixed bugs:**

- whipper doesn't name files .flac, which leads to it not being able to find ripped files [\#194](https://github.com/whipper-team/whipper/issues/194)
- Issues with finding offset [\#182](https://github.com/whipper-team/whipper/issues/182)
- failing unittests in systemd-nspawn container [\#157](https://github.com/whipper-team/whipper/issues/157)
- Regression: Unable to resume a failed rip [\#136](https://github.com/whipper-team/whipper/issues/136)
- "Catalog Number" incorrectly appended to "artist" instead of the Album name. [\#127](https://github.com/whipper-team/whipper/issues/127)
- Track "can't be ripped" but EAC can :\) [\#116](https://github.com/whipper-team/whipper/issues/116)
- ERROR: stopping task which is already stopped [\#59](https://github.com/whipper-team/whipper/issues/59)
- can't find accuraterip-checksum binary in morituri-uninstalled mode [\#47](https://github.com/whipper-team/whipper/issues/47)

**Closed issues:**

- using your own MusicBrainz server [\#172](https://github.com/whipper-team/whipper/issues/172)
- cdda2wav from cdrtools instead of cdparanoia [\#38](https://github.com/whipper-team/whipper/issues/38)

**Merged pull requests:**

- Fix appearance of template description text. [\#223](https://github.com/whipper-team/whipper/pull/223) ([calumchisholm](https://github.com/calumchisholm))
- Run whipper without installation [\#222](https://github.com/whipper-team/whipper/pull/222) ([vmx](https://github.com/vmx))
- Remove doc/release [\#218](https://github.com/whipper-team/whipper/pull/218) ([MerlijnWajer](https://github.com/MerlijnWajer))
- Fix resuming previous rips [\#217](https://github.com/whipper-team/whipper/pull/217) ([MerlijnWajer](https://github.com/MerlijnWajer))
- Switch to libcdio-cdparanoia \(from cdparanoia\) [\#213](https://github.com/whipper-team/whipper/pull/213) ([MerlijnWajer](https://github.com/MerlijnWajer))
- Convert docstrings to reStructuredText [\#211](https://github.com/whipper-team/whipper/pull/211) ([JoeLametta](https://github.com/JoeLametta))
- Enable connecting to a custom MusicBrainz server [\#210](https://github.com/whipper-team/whipper/pull/210) ([ghost](https://github.com/ghost))
- Fix recently introduced Python 3 incompatibility [\#199](https://github.com/whipper-team/whipper/pull/199) ([LingMan](https://github.com/LingMan))
- restore .flac extension [\#195](https://github.com/whipper-team/whipper/pull/195) ([RecursiveForest](https://github.com/RecursiveForest))
- Misc fixes [\#188](https://github.com/whipper-team/whipper/pull/188) ([ubitux](https://github.com/ubitux))
- AccurateRip V2 support [\#187](https://github.com/whipper-team/whipper/pull/187) ([RecursiveForest](https://github.com/RecursiveForest))
- Solve all flake8 warnings [\#163](https://github.com/whipper-team/whipper/pull/163) ([JoeLametta](https://github.com/JoeLametta))
- Minor touchups [\#161](https://github.com/whipper-team/whipper/pull/161) ([Freso](https://github.com/Freso))
- Stop allowing flake8 to fail in Travis CI [\#160](https://github.com/whipper-team/whipper/pull/160) ([Freso](https://github.com/Freso))
- Fix division by zero [\#159](https://github.com/whipper-team/whipper/pull/159) ([sqozz](https://github.com/sqozz))
- Fix artist name [\#156](https://github.com/whipper-team/whipper/pull/156) ([gorgobacka](https://github.com/gorgobacka))
- Detect and handle CD-R discs [\#154](https://github.com/whipper-team/whipper/pull/154) ([gorgobacka](https://github.com/gorgobacka))
- Disambiguate on release [\#153](https://github.com/whipper-team/whipper/pull/153) ([Freso](https://github.com/Freso))
- Add flake8 testing to CI [\#151](https://github.com/whipper-team/whipper/pull/151) ([Freso](https://github.com/Freso))
- Clean up files in misc/ [\#150](https://github.com/whipper-team/whipper/pull/150) ([Freso](https://github.com/Freso))
- Update .gitignore [\#148](https://github.com/whipper-team/whipper/pull/148) ([Freso](https://github.com/Freso))
- Fix references to morituri. [\#109](https://github.com/whipper-team/whipper/pull/109) ([Freso](https://github.com/Freso))

## [v0.5.1](https://github.com/whipper-team/whipper/tree/v0.5.1) (2017-04-24)
[Full Changelog](https://github.com/whipper-team/whipper/compare/v0.5.0...v0.5.1)

**Fixed bugs:**

- 0.5.0 Release init.py version number not updated [\#147](https://github.com/whipper-team/whipper/issues/147)

## [v0.5.0](https://github.com/whipper-team/whipper/tree/v0.5.0) (2017-04-24)
[Full Changelog](https://github.com/whipper-team/whipper/compare/v0.4.2...v0.5.0)

**Implemented enhancements:**

- overly verbose warning logging [\#131](https://github.com/whipper-team/whipper/issues/131)
- Check that whipper deals properly with CD pre-emphasis [\#120](https://github.com/whipper-team/whipper/issues/120)
- Remove gstreamer dependency [\#29](https://github.com/whipper-team/whipper/issues/29)

**Fixed bugs:**

- Final track rip failure due to file size mismatch [\#146](https://github.com/whipper-team/whipper/issues/146)
- Fails to rip if MB Release doesn't have a release date/year [\#133](https://github.com/whipper-team/whipper/issues/133)
- fb271f08cdee877795091065c344dcc902d1dcbf breaks HEAD [\#129](https://github.com/whipper-team/whipper/issues/129)
- 'whipper drive list' returns a suggestion to run 'rip offset find' [\#112](https://github.com/whipper-team/whipper/issues/112)
- EmptyError\('not a single buffer gotten',\) [\#101](https://github.com/whipper-team/whipper/issues/101)
- Julie Roberts bug [\#74](https://github.com/whipper-team/whipper/issues/74)

**Merged pull requests:**

- Remove notes related to GStreamer flacparse [\#140](https://github.com/whipper-team/whipper/pull/140) ([Freso](https://github.com/Freso))
- Prevent a crash if MusicBrainz release date is missing [\#139](https://github.com/whipper-team/whipper/pull/139) ([ribbons](https://github.com/ribbons))
- program: do not fetch 4 times musicbrainz metadata [\#134](https://github.com/whipper-team/whipper/pull/134) ([ubitux](https://github.com/ubitux))
- Fix Travis CI build failures [\#132](https://github.com/whipper-team/whipper/pull/132) ([JoeLametta](https://github.com/JoeLametta))
- Rip out all code that uses gstreamer [\#130](https://github.com/whipper-team/whipper/pull/130) ([MerlijnWajer](https://github.com/MerlijnWajer))
- Add pre-emphasis status reporting to whipper's logfiles [\#124](https://github.com/whipper-team/whipper/pull/124) ([JoeLametta](https://github.com/JoeLametta))
- Add gstreamer-less flac encoder and tagging [\#121](https://github.com/whipper-team/whipper/pull/121) ([MerlijnWajer](https://github.com/MerlijnWajer))
- Replace rip command suggestions with 'whipper' [\#114](https://github.com/whipper-team/whipper/pull/114) ([JoeLametta](https://github.com/JoeLametta))

## [v0.4.2](https://github.com/whipper-team/whipper/tree/v0.4.2) (2017-01-08)
[Full Changelog](https://github.com/whipper-team/whipper/compare/v0.4.1...v0.4.2)

**Implemented enhancements:**

- Whipper attempts to rip with no CD inserted [\#81](https://github.com/whipper-team/whipper/issues/81)

**Fixed bugs:**

- 0.4.1 Release created but version number in code not bumped [\#105](https://github.com/whipper-team/whipper/issues/105)

**Merged pull requests:**

- Amend previous tagged release [\#107](https://github.com/whipper-team/whipper/pull/107) ([JoeLametta](https://github.com/JoeLametta))
- Update links to Arch Linux AUR packages in README. [\#103](https://github.com/whipper-team/whipper/pull/103) ([Freso](https://github.com/Freso))

## [v0.4.1](https://github.com/whipper-team/whipper/tree/v0.4.1) (2017-01-06)
[Full Changelog](https://github.com/whipper-team/whipper/compare/v0.4.0...v0.4.1)

**Implemented enhancements:**

- Migrate away from the "rip" command [\#21](https://github.com/whipper-team/whipper/issues/21)
- Fixed README broken links and added a better changelog [\#90](https://github.com/whipper-team/whipper/pull/90) ([JoeLametta](https://github.com/JoeLametta))

**Merged pull requests:**

- Small cleanups of setup.py [\#102](https://github.com/whipper-team/whipper/pull/102) ([Freso](https://github.com/Freso))
- Persist False value for defeats\_cache correctly [\#98](https://github.com/whipper-team/whipper/pull/98) ([ribbons](https://github.com/ribbons))
- Update suggested commands given by `drive list` [\#97](https://github.com/whipper-team/whipper/pull/97) ([ribbons](https://github.com/ribbons))
- add url and license to setup.py [\#96](https://github.com/whipper-team/whipper/pull/96) ([RecursiveForest](https://github.com/RecursiveForest))
- remove configure.configure, use \_\_version\_\_, remove getRevision\(\) [\#94](https://github.com/whipper-team/whipper/pull/94) ([RecursiveForest](https://github.com/RecursiveForest))
- cdrdao no-disc ejection & --eject [\#93](https://github.com/whipper-team/whipper/pull/93) ([RecursiveForest](https://github.com/RecursiveForest))
- argparse & logging [\#92](https://github.com/whipper-team/whipper/pull/92) ([RecursiveForest](https://github.com/RecursiveForest))
- Update README.md [\#91](https://github.com/whipper-team/whipper/pull/91) ([pieqq](https://github.com/pieqq))
- soxi: remove self.\_path unused variable, mark dep as 'soxi' [\#89](https://github.com/whipper-team/whipper/pull/89) ([RecursiveForest](https://github.com/RecursiveForest))
- Fix spelling mistake in README.md [\#86](https://github.com/whipper-team/whipper/pull/86) ([takeshibaconsuzuki](https://github.com/takeshibaconsuzuki))
- Error reporting enhancements \(conditional-raise-instead-of-assert version\) [\#80](https://github.com/whipper-team/whipper/pull/80) ([chrysn](https://github.com/chrysn))
- Update top level informational files [\#71](https://github.com/whipper-team/whipper/pull/71) ([RecursiveForest](https://github.com/RecursiveForest))
- Use soxi instead of gstreamer to determine a track's length [\#67](https://github.com/whipper-team/whipper/pull/67) ([chrysn](https://github.com/chrysn))

## [v0.4.0](https://github.com/whipper-team/whipper/tree/v0.4.0) (2016-11-08)
[Full Changelog](https://github.com/whipper-team/whipper/compare/v0.3.0...v0.4.0)

**Fixed bugs:**

- wrong status code when giving up [\#57](https://github.com/whipper-team/whipper/issues/57)
- CD-TEXT issue [\#49](https://github.com/whipper-team/whipper/issues/49)

**Merged pull requests:**

- Invoke whipper by its name + Readme rewrite [\#70](https://github.com/whipper-team/whipper/pull/70) ([JoeLametta](https://github.com/JoeLametta))
- do not recalculate musicbrainz disc id for every getMusicBrainzDiscId… [\#69](https://github.com/whipper-team/whipper/pull/69) ([RecursiveForest](https://github.com/RecursiveForest))
- Directory [\#62](https://github.com/whipper-team/whipper/pull/62) ([RecursiveForest](https://github.com/RecursiveForest))
- undelete overzealously removed plugin initialisation [\#61](https://github.com/whipper-team/whipper/pull/61) ([RecursiveForest](https://github.com/RecursiveForest))
- Readme rewrite [\#60](https://github.com/whipper-team/whipper/pull/60) ([RecursiveForest](https://github.com/RecursiveForest))
- README.md: drop executable flag [\#55](https://github.com/whipper-team/whipper/pull/55) ([chrysn](https://github.com/chrysn))
- nuke-autohell [\#54](https://github.com/whipper-team/whipper/pull/54) ([RecursiveForest](https://github.com/RecursiveForest))
- standardise program/sox.py formatting, add test case, docstring [\#53](https://github.com/whipper-team/whipper/pull/53) ([RecursiveForest](https://github.com/RecursiveForest))
- replace cdrdao.py with much simpler version [\#52](https://github.com/whipper-team/whipper/pull/52) ([RecursiveForest](https://github.com/RecursiveForest))
- use setuptools, remove autohell, use raw make for src/ [\#51](https://github.com/whipper-team/whipper/pull/51) ([RecursiveForest](https://github.com/RecursiveForest))

## [v0.3.0](https://github.com/whipper-team/whipper/tree/v0.3.0) (2016-10-17)
[Full Changelog](https://github.com/whipper-team/whipper/compare/v0.2.4...v0.3.0)

**Fixed bugs:**

- UnicodeEncodeError [\#43](https://github.com/whipper-team/whipper/issues/43)
- Use a single standard for config/cache/state files [\#24](https://github.com/whipper-team/whipper/issues/24)

**Merged pull requests:**

- Sox [\#48](https://github.com/whipper-team/whipper/pull/48) ([RecursiveForest](https://github.com/RecursiveForest))
- Fast accuraterip checksum [\#37](https://github.com/whipper-team/whipper/pull/37) ([MerlijnWajer](https://github.com/MerlijnWajer))

## [v0.2.4](https://github.com/whipper-team/whipper/tree/v0.2.4) (2016-10-09)
[Full Changelog](https://github.com/whipper-team/whipper/compare/v0.2.3...v0.2.4)

**Implemented enhancements:**

- Don't allow ripping without an explicit offset, and make pycdio a required dependency [\#23](https://github.com/whipper-team/whipper/issues/23)
- Minimal makedepends for building [\#17](https://github.com/whipper-team/whipper/issues/17)
- Delete stale branches [\#7](https://github.com/whipper-team/whipper/issues/7)
- get rid of the gstreamer-0.10 dependency [\#2](https://github.com/whipper-team/whipper/issues/2)
- Merge 'fork' into 'master' [\#1](https://github.com/whipper-team/whipper/issues/1)

**Fixed bugs:**

- whipper fails to build on bash-compgen [\#25](https://github.com/whipper-team/whipper/issues/25)
- \[musicbrainz\] KeyError: 'disc' [\#22](https://github.com/whipper-team/whipper/issues/22)
- NameError: global name 'musicbrainz' is not defined [\#16](https://github.com/whipper-team/whipper/issues/16)
- Fix HTOA handling [\#14](https://github.com/whipper-team/whipper/issues/14)
- rip offset find seems to fail [\#4](https://github.com/whipper-team/whipper/issues/4)
- rip cd info seems to fail [\#3](https://github.com/whipper-team/whipper/issues/3)

**Merged pull requests:**

- Issue24 [\#42](https://github.com/whipper-team/whipper/pull/42) ([JoeLametta](https://github.com/JoeLametta))
- Update .travis.yml [\#39](https://github.com/whipper-team/whipper/pull/39) ([JoeLametta](https://github.com/JoeLametta))
- Fix issue \#23 [\#32](https://github.com/whipper-team/whipper/pull/32) ([JoeLametta](https://github.com/JoeLametta))
- Remove thomasvs' python-deps [\#31](https://github.com/whipper-team/whipper/pull/31) ([JoeLametta](https://github.com/JoeLametta))
- Include name of used logger into whipper's txt report [\#30](https://github.com/whipper-team/whipper/pull/30) ([JoeLametta](https://github.com/JoeLametta))
- PRE\_EMPHASIS [\#27](https://github.com/whipper-team/whipper/pull/27) ([RecursiveForest](https://github.com/RecursiveForest))
- Resolve case where \_peakdB is None [\#20](https://github.com/whipper-team/whipper/pull/20) ([chadberg](https://github.com/chadberg))
- Remove old musicbrainz dependency [\#12](https://github.com/whipper-team/whipper/pull/12) ([abendebury](https://github.com/abendebury))
- Travis build fix [\#10](https://github.com/whipper-team/whipper/pull/10) ([abendebury](https://github.com/abendebury))
- Fork [\#6](https://github.com/whipper-team/whipper/pull/6) ([abendebury](https://github.com/abendebury))

## [v0.2.3](https://github.com/whipper-team/whipper/tree/v0.2.3) (2014-07-16)
[Full Changelog](https://github.com/whipper-team/whipper/compare/v0.2.2...v0.2.3)

## [v0.2.2](https://github.com/whipper-team/whipper/tree/v0.2.2) (2013-07-30)
[Full Changelog](https://github.com/whipper-team/whipper/compare/v0.2.1...v0.2.2)

## [v0.2.1](https://github.com/whipper-team/whipper/tree/v0.2.1) (2013-07-15)
[Full Changelog](https://github.com/whipper-team/whipper/compare/v0.2.0...v0.2.1)

## [v0.2.0](https://github.com/whipper-team/whipper/tree/v0.2.0) (2013-01-20)


\* *This Change Log was automatically generated by [github_changelog_generator](https://github.com/skywinder/Github-Changelog-Generator)*
