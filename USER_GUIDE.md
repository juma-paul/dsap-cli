# DSAP User Guide

Master Data Structures & Algorithms with scientifically-proven spaced repetition.

This guide explains how to use DSAP to practice algorithm problems using spaced repetition so you retain problem-solving patterns long-term.

---

# Table of Contents

1. [Installation](#1-installation)
2. [Getting Started](#2-getting-started)
3. [Daily Workflow](#3-daily-workflow)
4. [Understanding the Interface](#4-understanding-the-interface)
5. [Command Reference](#5-command-reference)
6. [Configuration](#6-configuration)
7. [Problem Sets](#7-problem-sets)
8. [Custom Problems](#8-custom-problems)
9. [How SM-2 Spaced Repetition Works](#9-how-sm-2-spaced-repetition-works)
10. [Common Scenarios](#10-common-scenarios)
11. [Interview Prep Strategies](#11-interview-prep-strategies)
12. [Troubleshooting](#12-troubleshooting)
13. [Data Management](#13-data-management)

---

# 1. Installation

## Recommended (Isolated CLI Tool)

```bash
# Using uv (fastest)
uv tool install dsap-cli

# Using pipx (alternative)
pipx install dsap-cli
```

## Alternative (Global Install)

```bash
pip install dsap-cli
uv pip install dsap-cli
```

## Verify Installation

```bash
dsap --version
dsap --help
```

---

# 2. Getting Started

## Step 1: Load a Problem Set

```bash
dsap load --list
dsap load blind75
```

Output example:

```
Loaded 75 problems from Blind 75
```

## Step 2: Configure Preferences

```bash
dsap config preferred_set blind75
dsap config daily_goal 5
```

## Step 3: Start Your First Problem

```bash
dsap next
```

This will:

1. Show a problem
2. Optionally open it in your browser
3. Ask you to rate recall after solving

---

# 3. Daily Workflow

## Morning Routine

```bash
dsap stats
dsap review
```

## Adding New Problems

```bash
dsap next --new-only
```

or

```bash
dsap next
```

---

## Review Session Flow

```
Show problem
     ↓
Solve problem
     ↓
Return to terminal
     ↓
Rate recall (0-5)
     ↓
DSAP schedules next review
```

---

## Rating Your Recall

| Rating | Name           | When To Use                              | Effect                     |
|------:|----------------|-------------------------------------------|----------------------------|
| 5     | Perfect        | Instant recall                            | Interval grows significantly |
| 4     | Good           | Correct but required thinking             | Interval grows              |
| 3     | Hard           | Struggled but solved                      | Interval grows slightly     |
| 2     | Forgot         | Wrong but solution felt familiar          | Interval resets             |
| 1     | Blackout       | Wrong, barely recognized solution         | Interval resets             |
| 0     | Total Blackout | No memory of solution                     | Interval resets             |

Tip: Always rate honestly so the algorithm schedules reviews correctly.

---

# 4. Understanding the Interface

## Problem Display Example

```
Two Sum

https://leetcode.com/problems/two-sum/

Difficulty: Easy
Category: Arrays
Set: Blind 75

Status: Solved
Attempts: 3
EF: 2.60
Interval: 15 days
Next Review: 2026-03-20
```

### Key Metrics

| Metric | Meaning |
|------|---------|
| EF | Easiness factor representing difficulty for you |
| Interval | Days until next review |
| Attempts | Number of reviews completed |

---

## Stats Display

```bash
dsap stats
```

Example:

```
Total Problems: 75
Solved: 45
Due Today: 5
Due This Week: 12
Current Streak: 7
Best Streak: 14
```

### Difficulty Breakdown

| Difficulty | Solved | Total | Progress |
|------------|--------|-------|----------|
| Easy       | 15     | 20    | 75% |
| Medium     | 25     | 40    | 62% |
| Hard       | 5      | 15    | 33% |

---

# 5. Command Reference

## dsap next

Get the next recommended problem.

```
dsap next
dsap next --difficulty Medium
dsap next --set blind75
dsap next --new-only
```

Priority order:

1. Due problems
2. New problems
3. Hardest problems (lowest EF)

---

## dsap review

Start a review session.

```
dsap review
dsap review --limit 5
dsap review --set blind75
```

---

## dsap list

List problems with filters.

```
dsap list
dsap list --limit 100
dsap list --difficulty Hard
dsap list --category "Graphs"
dsap list --due
```

---

## dsap stats

```
dsap stats
```

Displays:

- problem counts
- review schedule
- streaks
- progress by difficulty

---

## dsap load

Load bundled or custom sets.

```
dsap load --list
dsap load blind75
dsap load neetcode150
dsap load grind75
dsap load ./custom.yaml
```

---

## dsap add

Add a custom problem.

```
dsap add
```

Prompts:

- title
- url
- difficulty
- category

---

## dsap config

View or update settings.

```
dsap config --list
dsap config preferred_set blind75
dsap config daily_goal 5
dsap config auto_open_browser false
```

---

## dsap reset

Reset problems or progress.

```
dsap reset --progress
dsap reset --all
dsap reset --set blind75 --progress
```

Warning: reset actions cannot be undone.

---

# 6. Configuration

| Setting | Default | Allowed Values | Description |
|--------|---------|----------------|-------------|
| preferred_set | None | blind75, neetcode150, grind75 | Default problem set |
| daily_goal | 5 | 1-100 | Target problems per day |
| preferred_difficulty | None | Easy, Medium, Hard | Difficulty filter |
| show_hints | true | true, false | Display hints |
| auto_open_browser | true | true, false | Open problems in browser |

---

# 7. Problem Sets

| Set | Problems | Description |
|----|----------|-------------|
| blind75 | 75 | Core interview problems |
| neetcode150 | 150 | Comprehensive curriculum |
| grind75 | 75 | Flexible study roadmap |

Load sets:

```
dsap load blind75
dsap load neetcode150
```

---

# 8. Custom Problems

Add one problem:

```
dsap add
```

Create a YAML set:

```yaml
metadata:
  name: "My Custom Set"

categories:
  - name: Arrays
    problems:
      - title: Two Sum
        url: https://leetcode.com/problems/two-sum/
        difficulty: Easy
```

Load it:

```
dsap load my-problems.yaml
```

---

# 9. How SM-2 Works

DSAP uses the SM-2 spaced repetition algorithm.

Typical interval growth:

```
1 day
6 days
15 days
38 days
95 days
```

After several successful reviews a problem may appear only every few months.

---

## Easiness Factor (EF)

Each problem has an EF value.

| EF Range | Meaning |
|--------|---------|
| 2.5+ | Easy for you |
| 2.0-2.5 | Moderate difficulty |
| 1.3-2.0 | Hard for you |

Lower EF → shorter review intervals.

---

# 10. Common Scenarios

## Starting From Scratch

```
dsap load blind75
dsap config preferred_set blind75
dsap next --new-only
```

---

## Too Many Reviews

```
dsap stats
dsap review --limit 10
```

Focus on clearing reviews first.

---

## Practice a Specific Topic

```
dsap next --category "Dynamic Programming"
```

---

# 11. Interview Prep Strategies

### 2-Week Plan

| Week | Focus | Daily Goal |
|-----|------|-----------|
| Week 1 | Easy + Medium | 5-7 problems |
| Week 2 | Medium + Hard | 3-5 problems |

---

### 1-Month Plan

| Week | Focus |
|------|------|
| 1-2 | Easy problems |
| 3-4 | Medium problems |
| 5+ | Hard problems |

---

# 12. Troubleshooting

## No Problems Found

Load a set first.

```
dsap load blind75
```

---

## Command Not Found

Reinstall the CLI.

```
uv tool install dsap-cli --force
```

---

## Browser Not Opening

```
dsap config auto_open_browser true
```

---

# 13. Data Management

## File Locations

```
~/.dsap/
├── dsap.db
└── config.json
```

---

## Backup Data

```
cp -r ~/.dsap ~/.dsap-backup
```

---

## Restore Data

```
rm -rf ~/.dsap
cp -r ~/.dsap-backup ~/.dsap
```

---

## Uninstall Completely

```
uv tool uninstall dsap-cli
rm -rf ~/.dsap
```

---

# Quick Reference

```
Daily

dsap stats
dsap review
dsap next

Setup

dsap load blind75
dsap config preferred_set blind75

Filters

--set
--difficulty
--category
--limit
--new-only
--due
```

For full command help:

```
dsap --help
dsap <command> --help
```
