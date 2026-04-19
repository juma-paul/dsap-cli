# Changelog

All notable changes to DSAP will be documented here.

## [1.0.2] - 2026-04-19

### Fixed
- README now displays correctly on PyPI (images and links)

## [1.0.1] - 2026-04-18

### Fixed
- Database error when saving review progress

## [1.0.0] - 2026-04-18

First stable release.

### Features
- SM-2 spaced repetition algorithm for optimal review scheduling
- Curated problem sets: Blind 75, NeetCode 150, Grind 75
- CLI commands: `review`, `next`, `list`, `stats`, `load`, `add`, `config`, `reset`
- Rich terminal UI with clickable LeetCode links
- Progress tracking with streaks and statistics
- Custom problem sets via YAML files
- Configurable preferences (daily goal, difficulty filter, auto-open browser)

### Technical
- Python 3.10-3.13 support
- Type hints throughout (mypy strict mode)
- 134 unit tests
- Auto-versioning from git tags

## [0.1.0] - 2026-03-08

Initial release.

---

[1.0.2]: https://github.com/juma-paul/dsap-cli/compare/v1.0.1...v1.0.2
[1.0.1]: https://github.com/juma-paul/dsap-cli/compare/v1.0.0...v1.0.1
[1.0.0]: https://github.com/juma-paul/dsap-cli/compare/v0.1.0...v1.0.0
[0.1.0]: https://github.com/juma-paul/dsap-cli/releases/tag/v0.1.0
