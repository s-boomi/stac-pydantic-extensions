# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

## [0.2.3.a] - 2026-09-18

### Fixed

- Datacube not imported in registry

## [0.2.2] - 2026-09-17

### Fixed

- Issues on original test fixture of `projection`.


## [0.2.1] - 2026-09-17

### Fixed

- Validation issues on CRS: didn't accept extraterrestrial references.


## [0.2.0] - 2026-09-16

### Added

- Created helper for collection summaries

### Fixed

- `projection` would return BBox validation errors over non-Mercator projections. This has been relaxed.
- Relaxed the rigid rules of Projjson to avoid more complexity


## [0.1.1] - 2026-09-15

### Fixed

- `ssys:target_class` now accepts both a singular value (Item) and a list of
  values (Collection `summaries`), matching how STAC Collections summarize
  categorical Item properties as Sets.


## [0.1.0] - 2026-08-08

### Added

- Initial project release.
