# DSAP User Guide

Detailed reference for DSAP users. For installation and quick start, see README.md.

---

## Table of Contents

1. [Daily Workflow](#daily-workflow)
2. [Understanding the Interface](#understanding-the-interface)
3. [Command Details](#command-details)
4. [Custom Problems](#custom-problems)
5. [Common Scenarios](#common-scenarios)
6. [Interview Prep Strategies](#interview-prep-strategies)
7. [Troubleshooting](#troubleshooting)
8. [Data Management](#data-management)

---

## Daily Workflow

### Morning Routine

```bash
dsap stats    # Check what's due
dsap review   # Clear due reviews first
```

### Adding New Problems

```bash
dsap next --new-only   # Only show unreviewed problems
```

### Review Session Flow

```
Show problem
     |
Solve problem (on LeetCode)
     |
Return to terminal
     |
Rate recall (0-5)
     |
DSAP schedules next review
```

### Rating Your Recall

| Rating | Name | When To Use | Effect |
|-------:|------|-------------|--------|
| 5 | Perfect | Instant recall | Interval grows significantly |
| 4 | Good | Correct but required thinking | Interval grows |
| 3 | Hard | Struggled but solved | Interval grows slightly |
| 2 | Forgot | Wrong but solution felt familiar | Interval resets |
| 1 | Blackout | Wrong, barely recognized solution | Interval resets |
| 0 | Total Blackout | No memory of solution | Interval resets |

Rate honestly so the algorithm schedules reviews correctly.

---

## Understanding the Interface

### Problem Display

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
|--------|---------|
| EF | Easiness factor - lower means harder for you |
| Interval | Days until next scheduled review |
| Attempts | Total number of reviews completed |

### Stats Display

```
Total Problems: 75
Solved: 45
Due Today: 5
Due This Week: 12
Current Streak: 7
Best Streak: 14
```

---

## Command Details

### dsap next

Get the next recommended problem.

```bash
dsap next                        # Default recommendation
dsap next --difficulty Medium    # Filter by difficulty
dsap next --set blind75          # Filter by set
dsap next --new-only             # Only unreviewed problems
dsap next --category "Graphs"    # Filter by category
```

Priority order:
1. Due problems (most overdue first)
2. New problems (never reviewed)
3. Hardest problems (lowest EF)

### dsap review

Start a review session with multiple problems.

```bash
dsap review              # All due problems
dsap review --limit 5    # Limit to 5 problems
dsap review --set blind75
```

### dsap list

Browse problems with filters.

```bash
dsap list                         # All problems
dsap list --limit 100             # Limit results
dsap list --difficulty Hard       # Filter difficulty
dsap list --category "Graphs"     # Filter category
dsap list --due                   # Only due problems
dsap list --set neetcode150       # Filter by set
```

### dsap reset

Reset progress (use with caution).

```bash
dsap reset --progress              # Reset all progress, keep problems
dsap reset --all                   # Delete everything
dsap reset --set blind75 --progress  # Reset one set's progress
```

Warning: Reset actions cannot be undone.

---

## Custom Problems

### Add Single Problem

```bash
dsap add
```

Prompts for: title, url, difficulty, category

### Create YAML Set

```yaml
metadata:
  name: "My Custom Set"

categories:
  - name: Arrays
    problems:
      - title: Two Sum
        url: https://leetcode.com/problems/two-sum/
        difficulty: Easy
        tags:
          - array
          - hash-table

  - name: Graphs
    problems:
      - title: Number of Islands
        url: https://leetcode.com/problems/number-of-islands/
        difficulty: Medium
```

Load custom set:

```bash
dsap load ./my-problems.yaml
```

---

## Common Scenarios

### Starting Fresh

```bash
dsap load blind75
dsap config preferred_set blind75
dsap next --new-only
```

### Too Many Due Reviews

Focus on clearing the backlog:

```bash
dsap stats                 # Check how many are due
dsap review --limit 10     # Clear 10 at a time
```

### Practice Specific Topic

```bash
dsap next --category "Dynamic Programming"
dsap list --category "Trees" --due
```

### Switching Problem Sets

```bash
dsap load neetcode150
dsap config preferred_set neetcode150
```

---

## Interview Prep Strategies

### 2-Week Intensive Plan

| Week | Focus | Daily Goal |
|------|-------|------------|
| 1 | Easy + Medium | 5-7 problems |
| 2 | Medium + Hard | 3-5 problems |

### 1-Month Gradual Plan

| Week | Focus |
|------|-------|
| 1-2 | Easy problems, build foundation |
| 3-4 | Medium problems, pattern recognition |
| 5+ | Hard problems, edge cases |

### Day Before Interview

```bash
dsap review --limit 5   # Light review
dsap stats              # Check your progress
```

Focus on problems you've struggled with (low EF).

---

## Troubleshooting

### No Problems Found

Load a problem set first:

```bash
dsap load blind75
```

### Command Not Found

Reinstall:

```bash
uv tool install dsap-cli --force
```

### Browser Not Opening

Check configuration:

```bash
dsap config auto_open_browser true
```

### Database Corrupted

Restore from backup or reset:

```bash
dsap reset --all
dsap load blind75
```

---

## Data Management

### File Locations

```
~/.dsap/
├── dsap.db       # SQLite database (problems, progress)
└── config.json   # User preferences
```

### Backup

```bash
cp -r ~/.dsap ~/.dsap-backup
```

### Restore

```bash
rm -rf ~/.dsap
cp -r ~/.dsap-backup ~/.dsap
```

### Export Progress

Query the database directly:

```bash
sqlite3 ~/.dsap/dsap.db "SELECT * FROM progress"
```

### Complete Uninstall

```bash
uv tool uninstall dsap-cli
rm -rf ~/.dsap
```

---

## Quick Reference

```
Daily:
  dsap stats
  dsap review
  dsap next

Filters:
  --set blind75
  --difficulty Medium
  --category "Arrays"
  --limit 10
  --new-only
  --due

Help:
  dsap --help
  dsap <command> --help
```
