# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [0.1.1] - 2026-09-17

### Changed

- Renamed the PyPI distribution from `py-goodreads` to `goodreads-async` after
  PyPI rejected the original name as too similar to an existing project. The
  `pygoodreads` import package is unchanged.

## [0.1.0] - 2026-09-17

### Added

- Initial asynchronous public shelf and reading-progress client.
- Typed models for profiles, books, shelves, progress, and reading snapshots.
- Safe profile URL and shelf-name parsing.
- CI, packaging, dependency auditing, and trusted PyPI publishing workflows.
