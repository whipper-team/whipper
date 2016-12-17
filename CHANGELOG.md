# Change Log

## [Unreleased](https://github.com/JoeLametta/whipper/tree/HEAD)

[Full Changelog](https://github.com/JoeLametta/whipper/compare/v0.4.0...HEAD)

**Merged pull requests:**

- soxi: remove self.\_path unused variable, mark dep as 'soxi' [\#89](https://github.com/JoeLametta/whipper/pull/89) ([RecursiveForest](https://github.com/RecursiveForest))
- Fix spelling mistake in README.md [\#86](https://github.com/JoeLametta/whipper/pull/86) ([takeshibaconsuzuki](https://github.com/takeshibaconsuzuki))
- Error reporting enhancements \(conditional-raise-instead-of-assert version\) [\#80](https://github.com/JoeLametta/whipper/pull/80) ([chrysn](https://github.com/chrysn))
- Update top level informational files [\#71](https://github.com/JoeLametta/whipper/pull/71) ([RecursiveForest](https://github.com/RecursiveForest))
- Use soxi instead of gstreamer to determine a track's length [\#67](https://github.com/JoeLametta/whipper/pull/67) ([chrysn](https://github.com/chrysn))

## [v0.4.0](https://github.com/JoeLametta/whipper/tree/v0.4.0) (2016-11-08)
[Full Changelog](https://github.com/JoeLametta/whipper/compare/v0.3.0...v0.4.0)

**Implemented enhancements:**

- Migrate away from the "rip" command [\#21](https://github.com/JoeLametta/whipper/issues/21)

**Fixed bugs:**

- wrong status code when giving up [\#57](https://github.com/JoeLametta/whipper/issues/57)
- CD-TEXT issue [\#49](https://github.com/JoeLametta/whipper/issues/49)

**Merged pull requests:**

- Invoke whipper by its name + Readme rewrite [\#70](https://github.com/JoeLametta/whipper/pull/70) ([JoeLametta](https://github.com/JoeLametta))
- do not recalculate musicbrainz disc id for every getMusicBrainzDiscId… [\#69](https://github.com/JoeLametta/whipper/pull/69) ([RecursiveForest](https://github.com/RecursiveForest))
- Directory [\#62](https://github.com/JoeLametta/whipper/pull/62) ([RecursiveForest](https://github.com/RecursiveForest))
- undelete overzealously removed plugin initialisation [\#61](https://github.com/JoeLametta/whipper/pull/61) ([RecursiveForest](https://github.com/RecursiveForest))
- Readme rewrite [\#60](https://github.com/JoeLametta/whipper/pull/60) ([RecursiveForest](https://github.com/RecursiveForest))
- README.md: drop executable flag [\#55](https://github.com/JoeLametta/whipper/pull/55) ([chrysn](https://github.com/chrysn))
- nuke-autohell [\#54](https://github.com/JoeLametta/whipper/pull/54) ([RecursiveForest](https://github.com/RecursiveForest))
- standardise program/sox.py formatting, add test case, docstring [\#53](https://github.com/JoeLametta/whipper/pull/53) ([RecursiveForest](https://github.com/RecursiveForest))
- replace cdrdao.py with much simpler version [\#52](https://github.com/JoeLametta/whipper/pull/52) ([RecursiveForest](https://github.com/RecursiveForest))
- use setuptools, remove autohell, use raw make for src/ [\#51](https://github.com/JoeLametta/whipper/pull/51) ([RecursiveForest](https://github.com/RecursiveForest))

## [v0.3.0](https://github.com/JoeLametta/whipper/tree/v0.3.0) (2016-10-17)
[Full Changelog](https://github.com/JoeLametta/whipper/compare/v0.2.4...v0.3.0)

**Fixed bugs:**

- UnicodeEncodeError [\#43](https://github.com/JoeLametta/whipper/issues/43)
- Use a single standard for config/cache/state files [\#24](https://github.com/JoeLametta/whipper/issues/24)

**Merged pull requests:**

- Sox [\#48](https://github.com/JoeLametta/whipper/pull/48) ([RecursiveForest](https://github.com/RecursiveForest))
- Fast accuraterip checksum [\#37](https://github.com/JoeLametta/whipper/pull/37) ([MerlijnWajer](https://github.com/MerlijnWajer))

## [v0.2.4](https://github.com/JoeLametta/whipper/tree/v0.2.4) (2016-10-09)
[Full Changelog](https://github.com/JoeLametta/whipper/compare/v0.2.3...v0.2.4)

**Implemented enhancements:**

- Don't allow ripping without an explicit offset, and make pycdio a required dependency [\#23](https://github.com/JoeLametta/whipper/issues/23)
- Delete stale branches [\#7](https://github.com/JoeLametta/whipper/issues/7)
- get rid of the gstreamer-0.10 dependency [\#2](https://github.com/JoeLametta/whipper/issues/2)

**Fixed bugs:**

- whipper fails to build on bash-compgen [\#25](https://github.com/JoeLametta/whipper/issues/25)
- \[musicbrainz\] KeyError: 'disc' [\#22](https://github.com/JoeLametta/whipper/issues/22)
- NameError: global name 'musicbrainz' is not defined [\#16](https://github.com/JoeLametta/whipper/issues/16)
- Fix HTOA handling [\#14](https://github.com/JoeLametta/whipper/issues/14)
- rip offset find seems to fail [\#4](https://github.com/JoeLametta/whipper/issues/4)
- rip cd info seems to fail [\#3](https://github.com/JoeLametta/whipper/issues/3)

**Closed issues:**

- Minimal makedepends for building [\#17](https://github.com/JoeLametta/whipper/issues/17)
- Merge 'fork' into 'master' [\#1](https://github.com/JoeLametta/whipper/issues/1)

**Merged pull requests:**

- Issue24 [\#42](https://github.com/JoeLametta/whipper/pull/42) ([JoeLametta](https://github.com/JoeLametta))
- Update .travis.yml [\#39](https://github.com/JoeLametta/whipper/pull/39) ([JoeLametta](https://github.com/JoeLametta))
- Fix issue \#23 [\#32](https://github.com/JoeLametta/whipper/pull/32) ([JoeLametta](https://github.com/JoeLametta))
- Remove thomasvs' python-deps [\#31](https://github.com/JoeLametta/whipper/pull/31) ([JoeLametta](https://github.com/JoeLametta))
- Include name of used logger into whipper's txt report [\#30](https://github.com/JoeLametta/whipper/pull/30) ([JoeLametta](https://github.com/JoeLametta))
- PRE\_EMPHASIS [\#27](https://github.com/JoeLametta/whipper/pull/27) ([RecursiveForest](https://github.com/RecursiveForest))
- Resolve case where \_peakdB is None [\#20](https://github.com/JoeLametta/whipper/pull/20) ([chadberg](https://github.com/chadberg))
- Remove old musicbrainz dependency [\#12](https://github.com/JoeLametta/whipper/pull/12) ([abendebury](https://github.com/abendebury))
- Travis build fix [\#10](https://github.com/JoeLametta/whipper/pull/10) ([abendebury](https://github.com/abendebury))
- Fork [\#6](https://github.com/JoeLametta/whipper/pull/6) ([abendebury](https://github.com/abendebury))

## [v0.2.3](https://github.com/JoeLametta/whipper/tree/v0.2.3) (2014-07-16)
[Full Changelog](https://github.com/JoeLametta/whipper/compare/v0.2.2...v0.2.3)

## [v0.2.2](https://github.com/JoeLametta/whipper/tree/v0.2.2) (2013-07-30)
[Full Changelog](https://github.com/JoeLametta/whipper/compare/v0.2.1...v0.2.2)

## [v0.2.1](https://github.com/JoeLametta/whipper/tree/v0.2.1) (2013-07-15)
[Full Changelog](https://github.com/JoeLametta/whipper/compare/v0.2.0...v0.2.1)

## [v0.2.0](https://github.com/JoeLametta/whipper/tree/v0.2.0) (2013-01-20)


\* *This Change Log was automatically generated by [github_changelog_generator](https://github.com/skywinder/Github-Changelog-Generator)* and hand edited by [JoeLametta](https://github.com/JoeLametta).
