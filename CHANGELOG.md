# Changelog

All notable changes to DSAP will be documented here.

## [1.1.1] - 2026-05-08

### Added

- `SM2State.days_until_review()` — returns days until next review as a
  signed integer: positive (days remaining), 0 (due today), negative (overdue).
- `Due` column in `dsap list` — shows relative timing (`in 7d`, `today`,
  `3d late`) at a glance.
- `DSAP_DB_PATH` environment variable — override the database path for
  scripting and isolated testing without touching your real database.
- CLI integration tests (`tests/test_cli.py`) — 28 end-to-end tests covering
  all commands via `CliRunner`.

### Fixed

- `dsap review` and `dsap list` showed raw `YYYY-MM-DD` dates for next
  review. Now displays human-readable relative strings: `Overdue by 3 days`,
  `Due today`, `In 7 days`.
- `dsap review` did not show problems due today if their scheduled time
  hadn't arrived yet (e.g. due at 23:00 but reviewing at 10:00). Due
  detection now compares calendar dates instead of exact datetimes, so
  anything due today appears immediately.

## [1.1.0] - 2026-05-08

### Changed

- `dsap next` now shows only new (never-attempted) problems. Previously it
  showed due problems and lowest-EF problems as fallbacks, overlapping with
  `dsap review`. The commands now have a clear contract:
  - `dsap next` = discover new problems you have never touched
  - `dsap review` = run your scheduled spaced-repetition session
- Removed `--new-only` flag from `dsap next` (new problems are now the default)
- Rating in `dsap next` is now always offered after displaying the problem,
  regardless of whether the browser was opened. Previously, rating was blocked
  when `auto_open_browser = false` in config.

### Fixed

- Problems with 0 attempts no longer appear in `dsap review`. Previously,
  `dsap next` created a partial progress record the moment a problem was
  displayed, causing it to appear as "due" in review even though it was never
  rated (root cause of "Maximum Product Subarray | Attempts: 0" showing in review).
- `solved` flag is now correctly set to 1 when rating quality >= 3 via the
  update path. Previously it was only set on first-ever INSERT; problems that
  had a partial progress record first would permanently show `solved = 0`.
- `first_attempted` timestamp is now set on the first actual rating even when
  updating an existing progress record (previously only set on INSERT).
- `dsap review`, `dsap next`, `dsap list`, and `dsap reset` no longer crash
  when `preferred_set` is not configured (the default). Previously raised
  `ValueError: Invalid problem set name`.
- "Reviewed" count in `dsap stats` now reflects problems with at least one
  actual attempt, not merely the presence of a progress record.
- Problem status now shows "New" instead of "In Progress" for any progress
  record where `attempts = 0`.

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

[1.1.1]: https://github.com/juma-paul/dsap-cli/compare/v1.1.0...v1.1.1
[1.1.0]: https://github.com/juma-paul/dsap-cli/compare/v1.0.2...v1.1.0
[1.0.2]: https://github.com/juma-paul/dsap-cli/compare/v1.0.1...v1.0.2
[1.0.1]: https://github.com/juma-paul/dsap-cli/compare/v1.0.0...v1.0.1
[1.0.0]: https://github.com/juma-paul/dsap-cli/compare/v0.1.0...v1.0.0
[0.1.0]: https://github.com/juma-paul/dsap-cli/releases/tag/v0.1.0
