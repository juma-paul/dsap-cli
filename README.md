

# Data Structures and Algorithms Practice (DSAP)

[![PyPI version](https://badge.fury.io/py/dsap-cli.svg)](https://pypi.org/project/dsap-cli/)
[![PyPI downloads](https://img.shields.io/pypi/dm/dsap-cli)](https://pypi.org/project/dsap-cli/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

DSAP is a terminal-first CLI that schedules coding interview problems using the **SM-2 spaced repetition algorithm**, helping you retain patterns long-term instead of forgetting them after solving once.

---

# Why DSAP?

Most developers preparing for technical interviews solve algorithm problems once and never revisit them.

As a result, they forget patterns they previously learned.

DSAP solves this by scheduling problems using **spaced repetition**, a learning technique proven to improve long-term memory.

Benefits:

- Retain algorithm patterns long-term
- Structured daily practice
- Automatic scheduling of reviews
- Focus on problems you’re about to forget

Instead of guessing what to practice next, **DSAP tells you exactly what to review**.

---

# Installation

```bash
# Recommended
uv tool install dsap-cli

# Alternatives
pipx install dsap-cli
pip install dsap-cli
```

Verify installation:

```bash
dsap --version
```

---

# Quick Start

```bash
# Load problems and set focus
dsap load blind75
dsap config preferred_set blind75

# Start practicing
dsap next
```

For the full workflow see:

```
USER_GUIDE.md
```

---

# Example Session

```
$ dsap next

📌 Next Problem
Two Sum (Easy)

Category: Arrays
Set: Blind 75

Open problem in browser? [y/N]

After solving, rate your recall:

5 - Perfect
4 - Good
3 - Hard
2 - Incorrect but remembered idea
1 - Incorrect
0 - Complete blackout
```

DSAP then schedules the next review automatically.

---

# Commands

| Command | Description |
|--------|-------------|
| `dsap next` | Get next recommended problem |
| `dsap review` | Review due problems in a session |
| `dsap list` | List problems with filters |
| `dsap stats` | View progress and statistics |
| `dsap load` | Load curated problem sets |
| `dsap config` | Manage configuration |
| `dsap reset` | Reset problems and/or progress |
| `dsap add` | Add a custom problem |

---

# Examples

```bash
# Filter by problem set
dsap next --set blind75
dsap review --set neetcode150

# Filter by difficulty
dsap next --difficulty Easy
dsap list --difficulty Hard

# Filter by category
dsap list --category "Dynamic Programming"

# Other options
dsap review --limit 5
dsap next --new-only
dsap list --due

# Reset progress
dsap reset --progress

# Reset a specific set
dsap reset --set blind75 --all
```

---

# Problem Sets

| Set | Problems | Description |
|----|----|----|
| `blind75` | 75 | Core interview essentials |
| `neetcode150` | 150 | Comprehensive curriculum |
| `grind75` | 75 | Flexible study roadmap |

```bash
dsap load --list
dsap load blind75
dsap load ./custom.yaml
```

---

# Configuration

```bash
dsap config --list
dsap config preferred_set blind75
dsap config daily_goal 5
dsap config preferred_difficulty Medium
dsap config auto_open_browser false
dsap config --reset
```

| Setting | Default | Description |
|----|----|----|
| `preferred_set` | None | Default problem set |
| `daily_goal` | 5 | Target problems per day |
| `preferred_difficulty` | None | Filter by difficulty |
| `show_hints` | true | Show problem hints |
| `auto_open_browser` | true | Open problems in browser |

---

# How It Works

DSAP implements the **SM-2 (SuperMemo 2)** spaced repetition algorithm.

After solving each problem, rate your recall from **0–5**.

| Rating | Meaning | Effect |
|----|----|----|
| 5 | Perfect | Interval grows |
| 4 | Good | Interval grows |
| 3 | Hard | Interval grows slowly |
| 0-2 | Forgot | Interval resets |

Typical interval progression:

```
1 day → 6 days → 15 days → 38 days → 95 days
```

After several successful reviews, problems reappear only every few months.

---

# Data Storage

DSAP stores all data locally:

```
~/.dsap/
├── dsap.db
└── config.json
```

To completely uninstall:

```bash
uv tool uninstall dsap-cli
rm -rf ~/.dsap
```

---

# Development

```bash
git clone https://github.com/juma-paul/dsap-cli.git
cd dsap-cli

uv sync --all-extras
uv run pytest
```

---

# Changelog

See the full release history in:

```
CHANGELOG.md
```

---

# License

MIT
