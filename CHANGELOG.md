# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),  
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

<!-- ---

## [Unreleased]

--- -->

## [0.1.0] - 2026-03-08

### Added

#### SM-2 Algorithm Implementation
- Full implementation of the SuperMemo 2 spaced repetition algorithm
- Quality ratings from 0–5 for flexible recall assessment
- Automatic interval calculation based on easiness factor
- Minimum easiness factor of 1.3 to prevent over-aggressive scheduling

#### Problem Management
- `dsap load` — Load curated problem sets (Blind 75, NeetCode 150, Grind 75)
- `dsap add` — Add custom problems with title, URL, difficulty, and category
- `dsap reset` — Reset problems and/or progress with flexible options
- Support for custom YAML problem set files
- Problem categorization by topic (Arrays, Trees, Graphs, etc.)
- Difficulty levels: Easy, Medium, Hard

#### Problem Sets
- Blind 75 — 75 essential interview problems
- NeetCode 150 — 150 comprehensive curriculum problems
- Grind 75 — 75 flexible study roadmap problems

#### Review System
- `dsap review` — Interactive review sessions with due problems
- `dsap next` — Get the next recommended problem
- Smart prioritization: due problems > new problems > hardest problems
- `--set` filter for focusing on specific problem sets
- `--difficulty` filter for targeting specific difficulty levels
- `--category` filter for practicing specific topics
- `--new-only` flag for getting only unattempted problems

#### Progress Tracking
- `dsap stats` — Comprehensive statistics dashboard
- Track solved problems, review counts, and streaks
- Per-difficulty breakdown (Easy / Medium / Hard)
- Due today and due this week counts
- `dsap list` — List problems with filters

#### Configuration
- `dsap config` — View and modify settings
- `preferred_set` — Set default problem set for all commands
- `preferred_difficulty` — Filter recommendations by difficulty
- `daily_goal` — Target problems per day
- `show_hints` — Toggle problem hints
- `auto_open_browser` — Toggle auto-opening problems in browser
- Flexible set name parsing (accepts `blind75`, `Blind 75`, `blind_75`, etc.)

#### CLI Features
- Built with Click for robust command-line interface
- Rich terminal UI with colors and tables
- Comprehensive `--help` for all commands

#### Documentation
- USER_GUIDE.md — Complete daily workflow guide
- Detailed README with examples

#### Data Storage
- SQLite database for reliable local storage
- Stored in `~/.dsap/dsap.db`
- Configuration in `~/.dsap/config.json`

### Technical

- Python 3.10+ support
- Type hints throughout the codebase (mypy strict mode)
- Pydantic v2 models for data validation
- Comprehensive test suite (134 tests)
- Google Python Style Guide compliance (ruff + pydocstyle)

---

[Unreleased]: https://github.com/juma-paul/dsap-cli/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/juma-paul/dsap-cli/releases/tag/v0.1.0