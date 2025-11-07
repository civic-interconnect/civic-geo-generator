# Changelog

All notable changes to this project will be documented in this file.

The format follows **[Keep a Changelog](https://keepachangelog.com/en/1.1.0/)**
and this project adheres to **[Semantic Versioning](https://semver.org/spec/v2.0.0.html)**.

---

## [Unreleased]

### Added
- (placeholder) Notes for the next release.

---

## [0.1.0] - 2025-11-06

### Added
- **Refactored** path resolution into a single `utils.paths` module as the central source of truth.
- **Unified** build, validate, and index workflows to use consistent directory logic.
- **Improved** CLI structure (`civic-gen`) with Typer, supporting `build`, `validate`, `index`, and `run` commands.
- **Enhanced** cross-platform compatibility and testing (no OS-specific paths).

---

## Notes on versioning and releases

- **SemVer policy**
  - **MAJOR** - breaking API/schema or CLI changes.
  - **MINOR** - backward-compatible additions and enhancements.
  - **PATCH** - documentation, tooling, or non-breaking fixes.
- Versions are driven by git tags via `setuptools_scm`.
  Tag the repository with `vX.Y.Z` to publish a release.
- Documentation and badges are updated per tag and aliased to **latest**.

[Unreleased]: https://github.com/civic-interconnect/civic-transparency-py-sdk/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/civic-interconnect/civic-transparency-py-sdk/releases/tag/v0.1.0
