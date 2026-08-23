# Changelog

All notable changes to this project are documented in this file.

## [0.1.2]

### Added

- Automated continuous delivery when the repository's `develop` branch is
  merged into `main`: validation, version tag creation, PyPI Trusted
  Publishing, and GitHub Release creation.
- PEP 440 version validation and duplicate-release safeguards for existing Git
  tags and PyPI releases.
- A required `develop` → `main` quality gate for a new version and an updated,
  non-empty changelog entry.

### Changed

- GitHub Release notes are now published directly from this changelog.

## [0.1.1a1]

### Added

- Register, inspect, refresh, and remove Jupyter kernels backed by uv-managed
  project environments.
- Continuous-delivery checks and Trusted Publishing support for PyPI releases.
