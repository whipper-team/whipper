# Change Log

## [Unreleased](https://github.com/whipper-team/whipper/tree/HEAD)

[Full Changelog](https://github.com/whipper-team/whipper/compare/v0.10.0...HEAD)

## [v0.10.0](https://github.com/whipper-team/whipper/tree/v0.10.0) (2021-05-17)

[Full Changelog](https://github.com/whipper-team/whipper/compare/v0.9.0...v0.10.0)

**Implemented enhancements:**

- Add checks and warnings for \(known\) cdparanoia's upstream bugs [\#495](https://github.com/whipper-team/whipper/issues/495) [[Design](https://github.com/whipper-team/whipper/labels/Design)]
- Allow configuring whether to auto close the drive's tray [\#488](https://github.com/whipper-team/whipper/issues/488)
- Better error handling for unconfigured drive offset [\#478](https://github.com/whipper-team/whipper/issues/478) [[Design](https://github.com/whipper-team/whipper/labels/Design)]
- WARNING:whipper.command.main:set\_hostname\(\) takes 1 positional argument but 2 were given [\#464](https://github.com/whipper-team/whipper/issues/464) [[Design](https://github.com/whipper-team/whipper/labels/Design)]
- Display release country in matching releases [\#451](https://github.com/whipper-team/whipper/issues/451)
- Ability to group multi-disc releases in a single folder [\#448](https://github.com/whipper-team/whipper/issues/448)
- Provide option to not use disambiguation in title [\#440](https://github.com/whipper-team/whipper/issues/440)
- test\_result\_logger.py: truly test all four cases of whipper version scheme [\#427](https://github.com/whipper-team/whipper/issues/427)
- more template options for filenames [\#401](https://github.com/whipper-team/whipper/issues/401)
- Always print output directory [\#393](https://github.com/whipper-team/whipper/issues/393) [[Design](https://github.com/whipper-team/whipper/labels/Design)]
- Provide better error message when there's no CD in the drive [\#385](https://github.com/whipper-team/whipper/issues/385) [[Design](https://github.com/whipper-team/whipper/labels/Design)]
- Change documentation from epydoc to reStructuredText [\#383](https://github.com/whipper-team/whipper/issues/383)
- Allow customization of maximum rip retries attempts value [\#349](https://github.com/whipper-team/whipper/issues/349)
- Save ISRCs from CD TOC [\#320](https://github.com/whipper-team/whipper/issues/320)
- PathFilter questions [\#313](https://github.com/whipper-team/whipper/issues/313)
- Let `debug musicbrainzngs` look up based on MusicBrainz Release ID in addition to Disc ID [\#251](https://github.com/whipper-team/whipper/issues/251)
- Ability to skip unrippable track [\#128](https://github.com/whipper-team/whipper/issues/128)
- add manpage [\#73](https://github.com/whipper-team/whipper/issues/73)
- Grab cover art [\#50](https://github.com/whipper-team/whipper/issues/50)
- cdda2wav from cdrtools instead of cdparanoia [\#38](https://github.com/whipper-team/whipper/issues/38)

**Fixed bugs:**

- Unable to find offset with a single-track cd [\#532](https://github.com/whipper-team/whipper/issues/532)
- Rip of CD fails to set "Various Artists" flac tag [\#518](https://github.com/whipper-team/whipper/issues/518)
- AccurateRipResponse test failures [\#515](https://github.com/whipper-team/whipper/issues/515)
- path\_filter\_whitespace not working [\#513](https://github.com/whipper-team/whipper/issues/513)
- got exception IndexError\('list index out of range'\) [\#512](https://github.com/whipper-team/whipper/issues/512)
- no CD detected, please insert one and retry [\#511](https://github.com/whipper-team/whipper/issues/511) [[Regression](https://github.com/whipper-team/whipper/labels/Regression)]
- whipper not finding the drive \(whipper docker install\) [\#499](https://github.com/whipper-team/whipper/issues/499)
- Missing .toc files when ripping a CD multiple times due to whipper ToC caching [\#486](https://github.com/whipper-team/whipper/issues/486)
- Change the docker alias in the readme to use {HOME} rather than ~ [\#482](https://github.com/whipper-team/whipper/issues/482)
- Musicbrainz lookup fails for multiple CD rip [\#477](https://github.com/whipper-team/whipper/issues/477)
- whipper drive analyze appears to be stuck [\#469](https://github.com/whipper-team/whipper/issues/469) [[Upstream Bug](https://github.com/whipper-team/whipper/labels/Upstream%20Bug)]
- Whipper configuration file: `cover_art` option does nothing [\#465](https://github.com/whipper-team/whipper/issues/465) [[Design](https://github.com/whipper-team/whipper/labels/Design)]
- Improve Docker instructions in README [\#452](https://github.com/whipper-team/whipper/issues/452)
- Whipper gives up even if 5th rip attempt is successful [\#449](https://github.com/whipper-team/whipper/issues/449)
- Don't include full file path in log files [\#445](https://github.com/whipper-team/whipper/issues/445) [[Regression](https://github.com/whipper-team/whipper/labels/Regression)]
- Whipper example config file: `%` character in inline comment causes `InterpolationSyntaxError` [\#443](https://github.com/whipper-team/whipper/issues/443)
- output directory isn't read [\#441](https://github.com/whipper-team/whipper/issues/441) [[Regression](https://github.com/whipper-team/whipper/labels/Regression)]
- Requests to accuraterip.com are missing a user agent which identifies whipper [\#439](https://github.com/whipper-team/whipper/issues/439)
- Bug: MusicBrainz lookup URL is hardcoded to always use https [\#437](https://github.com/whipper-team/whipper/issues/437)
- `whipper drive analyze` is broken on Python 3 [\#431](https://github.com/whipper-team/whipper/issues/431) [[Regression](https://github.com/whipper-team/whipper/labels/Regression)]
- Make it possible to build from tarball again [\#428](https://github.com/whipper-team/whipper/issues/428) [[Regression](https://github.com/whipper-team/whipper/labels/Regression)]
- TypeError: float argument required, not NoneType [\#402](https://github.com/whipper-team/whipper/issues/402)
- Drop whipper caching [\#335](https://github.com/whipper-team/whipper/issues/335)
- musicbrainz calculation fails on cd with data tracks that are not positioned at the end [\#289](https://github.com/whipper-team/whipper/issues/289)
- AttributeError: 'Namespace' object has no attribute 'offset' [\#230](https://github.com/whipper-team/whipper/issues/230) [[Regression](https://github.com/whipper-team/whipper/labels/Regression)]
- `'NoneType' object has no attribute '__getitem__'` after rip with current master \(a3e9260\) [\#196](https://github.com/whipper-team/whipper/issues/196)
- Use the track title instead the recoding title \(MusicBrainz related\) [\#192](https://github.com/whipper-team/whipper/issues/192)
- pygobject\_register\_sinkfunc is deprecated [\#45](https://github.com/whipper-team/whipper/issues/45)

**Merged pull requests:**

- Fixed error when ripping using `--keep-going` without specifying `--o… [\#537](https://github.com/whipper-team/whipper/pull/537) ([blueblots](https://github.com/blueblots))
- Add requested template variables [\#536](https://github.com/whipper-team/whipper/pull/536) ([JoeLametta](https://github.com/JoeLametta))
- Added --keep-going option to cd rip command [\#524](https://github.com/whipper-team/whipper/pull/524) ([blueblots](https://github.com/blueblots))
- Parameterise the UID of the worker user in the docker build file. [\#517](https://github.com/whipper-team/whipper/pull/517) ([unclealex72](https://github.com/unclealex72))
- Fix capitalization of "Health status" in rip log [\#510](https://github.com/whipper-team/whipper/pull/510) ([MasterOdin](https://github.com/MasterOdin))
- Tag audio tracks with ISRCs \(if available\) [\#509](https://github.com/whipper-team/whipper/pull/509) ([JoeLametta](https://github.com/JoeLametta))
- Provide better error message when there's no CD in the drive [\#507](https://github.com/whipper-team/whipper/pull/507) ([JoeLametta](https://github.com/JoeLametta))
- Add checks and warnings for \(known\) cdparanoia's upstream bugs [\#506](https://github.com/whipper-team/whipper/pull/506) ([JoeLametta](https://github.com/JoeLametta))
- Allow configuring whether to auto close the drive's tray [\#505](https://github.com/whipper-team/whipper/pull/505) ([JoeLametta](https://github.com/JoeLametta))
- Travis CI: Add Python 3.9 release candidate 1 [\#504](https://github.com/whipper-team/whipper/pull/504) ([cclauss](https://github.com/cclauss))
- Define libcdio version as environment variables in docker [\#498](https://github.com/whipper-team/whipper/pull/498) ([MasterOdin](https://github.com/MasterOdin))
- Add man pages. [\#490](https://github.com/whipper-team/whipper/pull/490) ([baldurmen](https://github.com/baldurmen))
- Restore the ability to use inline comments in config files [\#461](https://github.com/whipper-team/whipper/pull/461) ([neilmayhew](https://github.com/neilmayhew))
- Fix cd rip --max-retries option handling [\#460](https://github.com/whipper-team/whipper/pull/460) ([kevinoid](https://github.com/kevinoid))
- Fix crash fetching cover art for unknown album [\#459](https://github.com/whipper-team/whipper/pull/459) ([kevinoid](https://github.com/kevinoid))
- Fix cover file saving with /tmp on different FS [\#458](https://github.com/whipper-team/whipper/pull/458) ([kevinoid](https://github.com/kevinoid))
- Test all four cases of whipper version scheme [\#456](https://github.com/whipper-team/whipper/pull/456) ([ABCbum](https://github.com/ABCbum))
- Allow customization of maximum rip attempts value [\#455](https://github.com/whipper-team/whipper/pull/455) ([ABCbum](https://github.com/ABCbum))
- Update docker instructions to use --bind instead of -v. [\#454](https://github.com/whipper-team/whipper/pull/454) ([MartinPaulEve](https://github.com/MartinPaulEve))
- Use https and http appropriately when connecting to MusicBrainz [\#450](https://github.com/whipper-team/whipper/pull/450) ([ABCbum](https://github.com/ABCbum))
- Add PERFORMER & COMPOSER metadata tags to audio tracks \(if available\) [\#444](https://github.com/whipper-team/whipper/pull/444) ([ABCbum](https://github.com/ABCbum))
- Grab cover art from MusicBrainz/Cover Art Archive and add it to the resulting whipper rips [\#436](https://github.com/whipper-team/whipper/pull/436) ([ABCbum](https://github.com/ABCbum))
- Fix whipper's MusicBrainz Disc ID calculation for CDs with data tracks that are not positioned at the end of the disc  [\#435](https://github.com/whipper-team/whipper/pull/435) ([ABCbum](https://github.com/ABCbum))
- Fix failed\(\) task of AnalyzeTask \(program/cdparanoia\) [\#434](https://github.com/whipper-team/whipper/pull/434) ([Freso](https://github.com/Freso))
- Test against Python versions 3.6, 3.7, and 3.8 [\#433](https://github.com/whipper-team/whipper/pull/433) ([Freso](https://github.com/Freso))
- Allow whipper's mblookup command to look up information based on Release MBID [\#432](https://github.com/whipper-team/whipper/pull/432) ([ABCbum](https://github.com/ABCbum))
- Enable whipper to use track title [\#430](https://github.com/whipper-team/whipper/pull/430) ([ABCbum](https://github.com/ABCbum))
- Improve docstrings [\#389](https://github.com/whipper-team/whipper/pull/389) ([JoeLametta](https://github.com/JoeLametta))
- Drop whipper caching [\#336](https://github.com/whipper-team/whipper/pull/336) ([JoeLametta](https://github.com/JoeLametta))
- Rewrite PathFilter [\#324](https://github.com/whipper-team/whipper/pull/324) ([JoeLametta](https://github.com/JoeLametta))

## [v0.9.0](https://github.com/whipper-team/whipper/tree/v0.9.0) (2019-12-04)

[Full Changelog](https://github.com/whipper-team/whipper/compare/v0.8.0...v0.9.0)

**Fixed bugs:**

- Fix regression introduced due to Python 3 port [\#424](https://github.com/whipper-team/whipper/issues/424) [[Regression](https://github.com/whipper-team/whipper/labels/Regression)]
- Test failure when building a release [\#420](https://github.com/whipper-team/whipper/issues/420)
- Dockerfile is missing ruamel.yaml [\#419](https://github.com/whipper-team/whipper/issues/419)
- exception while reading CD [\#413](https://github.com/whipper-team/whipper/issues/413)
- Unable to find offset using specific CD. [\#252](https://github.com/whipper-team/whipper/issues/252)
- cdparanoia toc does not agree with cdrdao-toc, cd-paranoia also reports different \(but better\) lengths [\#175](https://github.com/whipper-team/whipper/issues/175) [[Upstream Bug](https://github.com/whipper-team/whipper/labels/Upstream%20Bug)]
- Port to Python 3 [\#78](https://github.com/whipper-team/whipper/issues/78)

**Merged pull requests:**

- Python 3 port [\#411](https://github.com/whipper-team/whipper/pull/411) ([ddevault](https://github.com/ddevault))

## [v0.8.0](https://github.com/whipper-team/whipper/tree/v0.8.0) (2019-10-27)

[Full Changelog](https://github.com/whipper-team/whipper/compare/v0.7.3...v0.8.0)

**Implemented enhancements:**

- Separate out Release in log into two value map [\#416](https://github.com/whipper-team/whipper/issues/416)
- Include MusicBrainz Release ID in the log file [\#381](https://github.com/whipper-team/whipper/issues/381)
- Note in the whipper output/log if development version was used [\#337](https://github.com/whipper-team/whipper/issues/337) [[Design](https://github.com/whipper-team/whipper/labels/Design)]
- read-toc progress information [\#299](https://github.com/whipper-team/whipper/issues/299) [[Design](https://github.com/whipper-team/whipper/labels/Design)]
- Look into adding more MusicBrainz identifiers to ripped files [\#200](https://github.com/whipper-team/whipper/issues/200)
- Specify supported version\(s\) of Python in setup.py [\#378](https://github.com/whipper-team/whipper/pull/378) ([Freso](https://github.com/Freso))

**Fixed bugs:**

- whipper bails out if MusicBrainz release group doesn’t have a type [\#396](https://github.com/whipper-team/whipper/issues/396)
- object has no attribute 'working\_directory' when running cd info [\#375](https://github.com/whipper-team/whipper/issues/375) [[Regression](https://github.com/whipper-team/whipper/labels/Regression)]
- Failure to rip CD: "ValueError: could not convert string to float: " [\#374](https://github.com/whipper-team/whipper/issues/374) [[Regression](https://github.com/whipper-team/whipper/labels/Regression)]
- "AttributeError: Program instance has no attribute '\_presult'" when ripping [\#369](https://github.com/whipper-team/whipper/issues/369) [[Regression](https://github.com/whipper-team/whipper/labels/Regression)]
- Drive analysis fails [\#361](https://github.com/whipper-team/whipper/issues/361)
- Eliminate warning "eject: CD-ROM tray close command failed" [\#354](https://github.com/whipper-team/whipper/issues/354) [[Design](https://github.com/whipper-team/whipper/labels/Design)]
- Flac file permissions [\#284](https://github.com/whipper-team/whipper/issues/284)

**Closed issues:**

- Add git/mercurial dependency to the README [\#386](https://github.com/whipper-team/whipper/issues/386)
- Rip while entering MusicBrainz data [\#360](https://github.com/whipper-team/whipper/issues/360)

**Merged pull requests:**

- Fix ripping discs with less than ten tracks [\#418](https://github.com/whipper-team/whipper/pull/418) ([mtdcr](https://github.com/mtdcr))
- Make getFastToc\(\) fast again [\#417](https://github.com/whipper-team/whipper/pull/417) ([mtdcr](https://github.com/mtdcr))
- Use ruamel.yaml for formatting and outputting rip .log file [\#415](https://github.com/whipper-team/whipper/pull/415) ([itismadness](https://github.com/itismadness))
- Handle missing self.options for whipper cd info [\#410](https://github.com/whipper-team/whipper/pull/410) ([JoeLametta](https://github.com/JoeLametta))
- Fix erroneous result message for whipper drive analyze [\#409](https://github.com/whipper-team/whipper/pull/409) ([JoeLametta](https://github.com/JoeLametta))
- Report eject's failures as logger warnings [\#408](https://github.com/whipper-team/whipper/pull/408) ([JoeLametta](https://github.com/JoeLametta))
- Set FLAC files permissions to 0644 [\#407](https://github.com/whipper-team/whipper/pull/407) ([JoeLametta](https://github.com/JoeLametta))
- Fix offset find command [\#406](https://github.com/whipper-team/whipper/pull/406) ([vmx](https://github.com/vmx))
- Make whipper not break on missing release type [\#398](https://github.com/whipper-team/whipper/pull/398) ([Freso](https://github.com/Freso))
- Set default for eject to: success [\#392](https://github.com/whipper-team/whipper/pull/392) ([gorgobacka](https://github.com/gorgobacka))
- Use eject value of the class again [\#391](https://github.com/whipper-team/whipper/pull/391) ([gorgobacka](https://github.com/gorgobacka))
- Convert documentation from epydoc to reStructuredText [\#387](https://github.com/whipper-team/whipper/pull/387) ([JoeLametta](https://github.com/JoeLametta))
- Include MusicBrainz Release URL in log output [\#382](https://github.com/whipper-team/whipper/pull/382) ([Freso](https://github.com/Freso))
- Fix critical regressions introduced in 3e79032 and 16b0d8d [\#371](https://github.com/whipper-team/whipper/pull/371) ([JoeLametta](https://github.com/JoeLametta))
- Use git to get whipper's version [\#370](https://github.com/whipper-team/whipper/pull/370) ([Freso](https://github.com/Freso))
- Handle artist MBIDs as multivalue tags [\#367](https://github.com/whipper-team/whipper/pull/367) ([Freso](https://github.com/Freso))
- Add Track, Release Group, and Work MBIDs to ripped files [\#366](https://github.com/whipper-team/whipper/pull/366) ([Freso](https://github.com/Freso))
- Refresh MusicBrainz JSON responses used for testing [\#365](https://github.com/whipper-team/whipper/pull/365) ([Freso](https://github.com/Freso))
- Clean up MusicBrainz nomenclature [\#364](https://github.com/whipper-team/whipper/pull/364) ([Freso](https://github.com/Freso))
- Fix misaligned output in command.mblookup [\#363](https://github.com/whipper-team/whipper/pull/363) ([Freso](https://github.com/Freso))
- Update accuraterip-checksum [\#362](https://github.com/whipper-team/whipper/pull/362) ([Freso](https://github.com/Freso))
- Require Developer Certificate of Origin sign-off [\#358](https://github.com/whipper-team/whipper/pull/358) ([JoeLametta](https://github.com/JoeLametta))
- Address warnings/errors from various static analysis tools [\#357](https://github.com/whipper-team/whipper/pull/357) ([JoeLametta](https://github.com/JoeLametta))
- Clarify format option for disc template [\#353](https://github.com/whipper-team/whipper/pull/353) ([rekh127](https://github.com/rekh127))
- Refactor cdrdao toc/table functions into Task and provide progress output [\#345](https://github.com/whipper-team/whipper/pull/345) ([jtl999](https://github.com/jtl999))
- accuraterip-checksum: convert to python C extension [\#274](https://github.com/whipper-team/whipper/pull/274) ([mtdcr](https://github.com/mtdcr))

## [v0.7.3](https://github.com/whipper-team/whipper/tree/v0.7.3) (2018-12-14)

[Full Changelog](https://github.com/whipper-team/whipper/compare/v0.7.2...v0.7.3)

**Implemented enhancements:**

- Write musicbrainz\_discid tag when disc is unknown [\#280](https://github.com/whipper-team/whipper/issues/280)
- Write .toc files in addition to .cue files to support cdrdao and non-compliant .cue sheets [\#214](https://github.com/whipper-team/whipper/issues/214)

**Fixed bugs:**

- Error when parsing log file due to left pad track number [\#340](https://github.com/whipper-team/whipper/issues/340)
- Failing AccurateRipResponse tests [\#333](https://github.com/whipper-team/whipper/issues/333) [[Regression](https://github.com/whipper-team/whipper/labels/Regression)]
- CRITICAL:whipper.command.cd:output directory is a finished rip output directory [\#287](https://github.com/whipper-team/whipper/issues/287)
- Possible HTOA error [\#281](https://github.com/whipper-team/whipper/issues/281) [[Upstream Bug](https://github.com/whipper-team/whipper/labels/Upstream%20Bug)]
- Disc template KeyError [\#279](https://github.com/whipper-team/whipper/issues/279)
- Enhanced CD causes computer to freeze. [\#256](https://github.com/whipper-team/whipper/issues/256) [[Upstream Bug](https://github.com/whipper-team/whipper/labels/Upstream%20Bug)]
- Unicode issues [\#215](https://github.com/whipper-team/whipper/issues/215)
- whipper offset find exception [\#208](https://github.com/whipper-team/whipper/issues/208)
- ZeroDivisionError: float division by zero [\#202](https://github.com/whipper-team/whipper/issues/202)
- Allow plugins from system directories [\#135](https://github.com/whipper-team/whipper/issues/135) [[Regression](https://github.com/whipper-team/whipper/labels/Regression)]

**Closed issues:**

- use standard logging [\#303](https://github.com/whipper-team/whipper/issues/303) [[Design](https://github.com/whipper-team/whipper/labels/Design)]

**Merged pull requests:**

- Discover plugins in system directories too [\#348](https://github.com/whipper-team/whipper/pull/348) ([JoeLametta](https://github.com/JoeLametta))
- Avoid zero padding in logger track numbers [\#341](https://github.com/whipper-team/whipper/pull/341) ([itismadness](https://github.com/itismadness))
- Update failing AccurateRipResponse tests [\#334](https://github.com/whipper-team/whipper/pull/334) ([JoeLametta](https://github.com/JoeLametta))
- Replace sys.std{out,err} statements with logger/print calls [\#331](https://github.com/whipper-team/whipper/pull/331) ([JoeLametta](https://github.com/JoeLametta))
- Add Probot apps to improve workflow [\#329](https://github.com/whipper-team/whipper/pull/329) ([JoeLametta](https://github.com/JoeLametta))
- Raise exception when cdparanoia can't read any frames [\#328](https://github.com/whipper-team/whipper/pull/328) ([JoeLametta](https://github.com/JoeLametta))
- Prevent exception in offset find [\#327](https://github.com/whipper-team/whipper/pull/327) ([JoeLametta](https://github.com/JoeLametta))
- Fix template validation error [\#325](https://github.com/whipper-team/whipper/pull/325) ([JoeLametta](https://github.com/JoeLametta))
- Fix UnicodeEncodeError with non ASCII MusicBrainz's catalog numbers [\#323](https://github.com/whipper-team/whipper/pull/323) ([JoeLametta](https://github.com/JoeLametta))
- Raise exception if template has invalid variables [\#322](https://github.com/whipper-team/whipper/pull/322) ([JoeLametta](https://github.com/JoeLametta))
- Preserve ToC file generated by cdrdao [\#321](https://github.com/whipper-team/whipper/pull/321) ([JoeLametta](https://github.com/JoeLametta))

## [v0.7.2](https://github.com/whipper-team/whipper/tree/v0.7.2) (2018-10-31)

[Full Changelog](https://github.com/whipper-team/whipper/compare/v0.7.1...v0.7.2)

**Implemented enhancements:**

- automatically build Docker images [\#301](https://github.com/whipper-team/whipper/issues/301)

**Fixed bugs:**

- UnicodeEncodeError: 'ascii' codec can't encode characters in position 17-18: ordinal not in range\(128\) [\#315](https://github.com/whipper-team/whipper/issues/315)

**Merged pull requests:**

- Explicitly encode path as UTF-8 in truncate\_filename\(\) [\#319](https://github.com/whipper-team/whipper/pull/319) ([Freso](https://github.com/Freso))
- Add AppStream metainfo.xml file [\#318](https://github.com/whipper-team/whipper/pull/318) ([Freso](https://github.com/Freso))

## [v0.7.1](https://github.com/whipper-team/whipper/tree/v0.7.1) (2018-10-23)

[Full Changelog](https://github.com/whipper-team/whipper/compare/v0.7.0...v0.7.1)

**Implemented enhancements:**

- Disable eject button when ripping [\#308](https://github.com/whipper-team/whipper/issues/308)
- Add cdparanoia version to log file [\#267](https://github.com/whipper-team/whipper/issues/267)
- Add a requirements.txt file [\#221](https://github.com/whipper-team/whipper/issues/221)

**Fixed bugs:**

- TypeError on whipper offset find [\#263](https://github.com/whipper-team/whipper/issues/263)
- Remove whipper's retag feature [\#262](https://github.com/whipper-team/whipper/issues/262)
- ImportError: libcdio.so.16: cannot open shared object file: No such file or directory [\#229](https://github.com/whipper-team/whipper/issues/229)
- Catch DNS error [\#206](https://github.com/whipper-team/whipper/issues/206)
- Limit length of filenames [\#197](https://github.com/whipper-team/whipper/issues/197)
- Loggers [\#117](https://github.com/whipper-team/whipper/issues/117)

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

- Simple message while reading TOC [\#257](https://github.com/whipper-team/whipper/issues/257)

**Fixed bugs:**

- cd rip   is not able to rip the last track [\#203](https://github.com/whipper-team/whipper/issues/203) [[Upstream Bug](https://github.com/whipper-team/whipper/labels/Upstream%20Bug)]
- CD-ROM powers off during rip command. [\#189](https://github.com/whipper-team/whipper/issues/189) [[Upstream Bug](https://github.com/whipper-team/whipper/labels/Upstream%20Bug)]
- Various ripping issues [\#179](https://github.com/whipper-team/whipper/issues/179)
- whipper not picking up all settings in whipper.conf [\#99](https://github.com/whipper-team/whipper/issues/99)

**Merged pull requests:**

- Small readme cleanups [\#250](https://github.com/whipper-team/whipper/pull/250) ([RecursiveForest](https://github.com/RecursiveForest))
- Remove debug commands, add mblookup command [\#249](https://github.com/whipper-team/whipper/pull/249) ([RecursiveForest](https://github.com/RecursiveForest))
- Remove reference to Copr repository [\#248](https://github.com/whipper-team/whipper/pull/248) ([mruszczyk](https://github.com/mruszczyk))
- Revert "Convert docstrings to reStructuredText" [\#246](https://github.com/whipper-team/whipper/pull/246) ([RecursiveForest](https://github.com/RecursiveForest))
- remove -T/--toc-pickle [\#245](https://github.com/whipper-team/whipper/pull/245) ([RecursiveForest](https://github.com/RecursiveForest))
- credit four major developers by line count [\#243](https://github.com/whipper-team/whipper/pull/243) ([RecursiveForest](https://github.com/RecursiveForest))
- remove radon reports [\#242](https://github.com/whipper-team/whipper/pull/242) ([RecursiveForest](https://github.com/RecursiveForest))
- read command parameters from config sections [\#240](https://github.com/whipper-team/whipper/pull/240) ([RecursiveForest](https://github.com/RecursiveForest))
- fix CI build error with latest pycdio [\#233](https://github.com/whipper-team/whipper/pull/233) ([thomas-mc-work](https://github.com/thomas-mc-work))
- Removed reference to unused "profile = flac" config option \(issue \#99\) [\#231](https://github.com/whipper-team/whipper/pull/231) ([calumchisholm](https://github.com/calumchisholm))

## [v0.6.0](https://github.com/whipper-team/whipper/tree/v0.6.0) (2018-02-02)

[Full Changelog](https://github.com/whipper-team/whipper/compare/v0.5.1...v0.6.0)

**Implemented enhancements:**

- using your own MusicBrainz server [\#172](https://github.com/whipper-team/whipper/issues/172)
- Use 'Artist as credited' in filename instead of 'Artist in MusicBrainz' \(e.g. to solve \[unknown\]\) [\#155](https://github.com/whipper-team/whipper/issues/155)
- Declare supported Python version [\#152](https://github.com/whipper-team/whipper/issues/152)
- Identify media type in log file \(ie CD vs CD-R\) [\#137](https://github.com/whipper-team/whipper/issues/137)
- Rename the Python module [\#100](https://github.com/whipper-team/whipper/issues/100)
- libcdio-paranoia instead of cdparanoia [\#87](https://github.com/whipper-team/whipper/issues/87)
- Support both AccurateRip V1 and AccurateRip V2 at the same time [\#18](https://github.com/whipper-team/whipper/issues/18)

**Fixed bugs:**

- Error: NotFoundException message displayed while ripping an unknown disc [\#198](https://github.com/whipper-team/whipper/issues/198)
- whipper doesn't name files .flac, which leads to it not being able to find ripped files [\#194](https://github.com/whipper-team/whipper/issues/194)
- Issues with finding offset [\#182](https://github.com/whipper-team/whipper/issues/182) [[Upstream Bug](https://github.com/whipper-team/whipper/labels/Upstream%20Bug)]
- failing unittests in systemd-nspawn container [\#157](https://github.com/whipper-team/whipper/issues/157)
- Update doc/release or remove it [\#149](https://github.com/whipper-team/whipper/issues/149)
- Test HTOA peak value against 0 \(integer equality\) [\#143](https://github.com/whipper-team/whipper/issues/143)
- Regression: Unable to resume a failed rip [\#136](https://github.com/whipper-team/whipper/issues/136)
- "Catalog Number" incorrectly appended to "artist" instead of the Album name. [\#127](https://github.com/whipper-team/whipper/issues/127)
- Track "can't be ripped" but EAC can :\) [\#116](https://github.com/whipper-team/whipper/issues/116)
- ERROR: stopping task which is already stopped [\#59](https://github.com/whipper-team/whipper/issues/59)
- can't find accuraterip-checksum binary in morituri-uninstalled mode [\#47](https://github.com/whipper-team/whipper/issues/47)

**Merged pull requests:**

- Test HTOA peak value against 0 \(integer comparison\) [\#224](https://github.com/whipper-team/whipper/pull/224) ([JoeLametta](https://github.com/JoeLametta))
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

- Remove gstreamer dependency [\#29](https://github.com/whipper-team/whipper/issues/29)

**Fixed bugs:**

- Final track rip failure due to file size mismatch [\#146](https://github.com/whipper-team/whipper/issues/146) [[Upstream Bug](https://github.com/whipper-team/whipper/labels/Upstream%20Bug)]
- Fails to rip if MB Release doesn't have a release date/year [\#133](https://github.com/whipper-team/whipper/issues/133)
- overly verbose warning logging [\#131](https://github.com/whipper-team/whipper/issues/131) [[Design](https://github.com/whipper-team/whipper/labels/Design)]
- fb271f08cdee877795091065c344dcc902d1dcbf breaks HEAD [\#129](https://github.com/whipper-team/whipper/issues/129)
- 'whipper drive list' returns a suggestion to run 'rip offset find' [\#112](https://github.com/whipper-team/whipper/issues/112)
- EmptyError\('not a single buffer gotten',\) [\#101](https://github.com/whipper-team/whipper/issues/101)
- Julie Roberts bug [\#74](https://github.com/whipper-team/whipper/issues/74) [[Upstream Bug](https://github.com/whipper-team/whipper/labels/Upstream%20Bug)]

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

**Fixed bugs:**

- 0.4.1 Release created but version number in code not bumped [\#105](https://github.com/whipper-team/whipper/issues/105)
- Whipper attempts to rip with no CD inserted [\#81](https://github.com/whipper-team/whipper/issues/81)

**Merged pull requests:**

- Amend previous tagged release [\#107](https://github.com/whipper-team/whipper/pull/107) ([JoeLametta](https://github.com/JoeLametta))
- Update links to Arch Linux AUR packages in README. [\#103](https://github.com/whipper-team/whipper/pull/103) ([Freso](https://github.com/Freso))

## [v0.4.1](https://github.com/whipper-team/whipper/tree/v0.4.1) (2017-01-06)

[Full Changelog](https://github.com/whipper-team/whipper/compare/v0.4.0...v0.4.1)

**Closed issues:**

- Migrate away from the "rip" command [\#21](https://github.com/whipper-team/whipper/issues/21) [[Design](https://github.com/whipper-team/whipper/labels/Design)]

**Merged pull requests:**

- Small cleanups of setup.py [\#102](https://github.com/whipper-team/whipper/pull/102) ([Freso](https://github.com/Freso))
- Persist False value for defeats\_cache correctly [\#98](https://github.com/whipper-team/whipper/pull/98) ([ribbons](https://github.com/ribbons))
- Update suggested commands given by `drive list` [\#97](https://github.com/whipper-team/whipper/pull/97) ([ribbons](https://github.com/ribbons))
- add url and license to setup.py [\#96](https://github.com/whipper-team/whipper/pull/96) ([RecursiveForest](https://github.com/RecursiveForest))
- remove configure.configure, use \_\_version\_\_, remove getRevision\(\) [\#94](https://github.com/whipper-team/whipper/pull/94) ([RecursiveForest](https://github.com/RecursiveForest))
- cdrdao no-disc ejection & --eject [\#93](https://github.com/whipper-team/whipper/pull/93) ([RecursiveForest](https://github.com/RecursiveForest))
- argparse & logging [\#92](https://github.com/whipper-team/whipper/pull/92) ([RecursiveForest](https://github.com/RecursiveForest))
- Update README.md [\#91](https://github.com/whipper-team/whipper/pull/91) ([pieqq](https://github.com/pieqq))
- Fixed README broken links and added a better changelog [\#90](https://github.com/whipper-team/whipper/pull/90) ([JoeLametta](https://github.com/JoeLametta))
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
- get rid of the gstreamer-0.10 dependency [\#2](https://github.com/whipper-team/whipper/issues/2)

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

[Full Changelog](https://github.com/whipper-team/whipper/compare/e84361b6534a116445bd27b48708fff9ffb589e9...v0.2.0)



\* *This Changelog was automatically generated by [github_changelog_generator](https://github.com/github-changelog-generator/github-changelog-generator)*
