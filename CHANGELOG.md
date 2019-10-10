# Change Log
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/)
and this project adheres to [Semantic Versioning](http://semver.org/).

## [3.0.2] - 2019-10-10
### Changed
- Removed left over files
- Renamed commands from `*-marathon` to `marathon-*`
- Added license
- Released to PyPi

## [3.0.1] - 2019-10-10
- Failed release, ignore

## [3.0.0] - 2019-10-10
### Added
- command `check-marathon`
- CLI args: `--user`, `--password`,  `--https-verify`
- Travis CI with `pylint` & this `CHANGELOG.md`

### Changed
- rename command `deploy` io `deploy-marathon`
- rename main package `deploytool` to `marathon_deploy`
