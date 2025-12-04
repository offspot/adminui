# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.3.1] - 2025-12-04

### Fixed

- Classmethod typing not py3.12 compatible

## [1.3] - 2025-12-03

### Changed

- Using alpine python (3.12) instead of 3.14 from uv (#3)

## [1.2] - 2025-12-01

### Fixed

- WiFi profile not representative on Pi3B (#1)

### Changed

- Defaulting to INFO log level unless `DEBUG` ENV is present (#2)
- Using offspot-config 2.9.0

## [1.1] - 2025-12-01

### Changed

- Using offspot-config release

## [1.0] - 2025-11-29

### Added

- WiFi config change (Profile, SSID – if capability enabled, Passphrase)
- SSH service
- Links to known admin services
