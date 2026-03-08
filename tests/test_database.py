"""
Tests for Database Operations

These tests verify the SQLite database operations work correctly
for problems, progress tracking, and statistics.
"""

from datetime import datetime, timedelta
from pathlib import Path

import pytest

from dsap.database import Database
from dsap.models import Difficulty, Problem
from dsap.sm2 import SM2State


class TestDatabase:
    """Tests for Database class."""

    @pytest.fixture
    def db(self, tmp_path: Path) -> Database:
        """Create a temporary database."""
        db_path = tmp_path / "test.db"
        return Database(db_path=db_path)

    @pytest.fixture
    def sample_problem(self) -> Problem:
        """Create a sample problem for testing."""
        return Problem(
            title="Two Sum",
            url="https://leetcode.com/problems/two-sum/",
            difficulty=Difficulty.EASY,
            category="Arrays & Hashing",
            description="Find two numbers that sum to target",
            tags=["array", "hash-table"],
            problem_set="blind75",
            problem_number=1,
        )

    @pytest.fixture
    def db_with_problems(self, db: Database) -> Database:
        """Create database with multiple problems."""
        problems = [
            Problem(
                title="Two Sum",
                url="https://leetcode.com/problems/two-sum/",
                difficulty=Difficulty.EASY,
                category="Arrays & Hashing",
                problem_set="blind75",
                problem_number=1,
            ),
            Problem(
                title="Valid Anagram",
                url="https://leetcode.com/problems/valid-anagram/",
                difficulty=Difficulty.EASY,
                category="Arrays & Hashing",
                problem_set="blind75",
                problem_number=2,
            ),
            Problem(
                title="3Sum",
                url="https://leetcode.com/problems/3sum/",
                difficulty=Difficulty.MEDIUM,
                category="Two Pointers",
                problem_set="blind75",
                problem_number=3,
            ),
            Problem(
                title="Merge K Sorted Lists",
                url="https://leetcode.com/problems/merge-k-sorted-lists/",
                difficulty=Difficulty.HARD,
                category="Linked List",
                problem_set="blind75",
                problem_number=4,
            ),
        ]
        for p in problems:
            db.add_problem(p)
        return db


class TestProblemOperations(TestDatabase):
    """Tests for problem CRUD operations."""

    def test_add_problem(self, db: Database, sample_problem: Problem):
        """Add a problem and retrieve it."""
        problem_id = db.add_problem(sample_problem)
        assert problem_id > 0

        retrieved = db.get_problem(problem_id)
        assert retrieved is not None
        assert retrieved.title == "Two Sum"
        assert retrieved.difficulty == Difficulty.EASY
        assert retrieved.category == "Arrays & Hashing"

    def test_add_duplicate_url_raises(self, db: Database, sample_problem: Problem):
        """Adding duplicate URL raises IntegrityError."""
        db.add_problem(sample_problem)

        import sqlite3

        with pytest.raises(sqlite3.IntegrityError):
            db.add_problem(sample_problem)

    def test_add_problems_skips_duplicates(self, db: Database):
        """add_problems skips duplicates and returns count."""
        problems = [
            Problem(
                title="Two Sum",
                url="https://leetcode.com/problems/two-sum/",
                difficulty=Difficulty.EASY,
                category="Arrays",
            ),
            Problem(
                title="Three Sum",
                url="https://leetcode.com/problems/3sum/",
                difficulty=Difficulty.MEDIUM,
                category="Arrays",
            ),
        ]

        added = db.add_problems(problems)
        assert added == 2

        # Try adding again (should skip)
        added = db.add_problems(problems)
        assert added == 0

    def test_get_problem_not_found(self, db: Database):
        """get_problem returns None for non-existent ID."""
        assert db.get_problem(9999) is None

    def test_delete_problem(self, db: Database, sample_problem: Problem):
        """Delete a problem."""
        problem_id = db.add_problem(sample_problem)
        assert db.delete_problem(problem_id) is True
        assert db.get_problem(problem_id) is None

    def test_delete_nonexistent_problem(self, db: Database):
        """Delete non-existent problem returns False."""
        assert db.delete_problem(9999) is False

    def test_get_problems_all(self, db_with_problems: Database):
        """Get all problems."""
        results = db_with_problems.get_problems(limit=100)
        assert len(results) == 4

    def test_get_problems_by_difficulty(self, db_with_problems: Database):
        """Filter problems by difficulty."""
        easy = db_with_problems.get_problems(difficulty="Easy")
        assert len(easy) == 2
        assert all(p.difficulty == Difficulty.EASY for p, _ in easy)

    def test_get_problems_by_category(self, db_with_problems: Database):
        """Filter problems by category."""
        arrays = db_with_problems.get_problems(category="Arrays & Hashing")
        assert len(arrays) == 2

    def test_get_problems_limit(self, db_with_problems: Database):
        """Limit number of problems returned."""
        results = db_with_problems.get_problems(limit=2)
        assert len(results) == 2


class TestProgressOperations(TestDatabase):
    """Tests for progress tracking operations."""

    def test_update_progress_creates_new(
        self,
        db: Database,
        sample_problem: Problem,
    ):
        """update_progress creates new progress record."""
        problem_id = db.add_problem(sample_problem)

        sm2_state = SM2State(
            easiness_factor=2.6,
            interval=1,
            repetitions=1,
            next_review=datetime.now() + timedelta(days=1),
            last_reviewed=datetime.now(),
        )

        db.update_progress(problem_id, sm2_state, quality=5)

        # Verify progress was created
        results = db.get_problems()
        assert len(results) == 1
        _problem, progress = results[0]
        assert progress is not None
        assert progress.easiness_factor == 2.6
        assert progress.interval == 1
        assert progress.repetitions == 1

    def test_update_progress_updates_existing(
        self,
        db: Database,
        sample_problem: Problem,
    ):
        """update_progress updates existing progress."""
        problem_id = db.add_problem(sample_problem)

        # First review
        state1 = SM2State(
            easiness_factor=2.5,
            interval=1,
            repetitions=1,
        )
        db.update_progress(problem_id, state1, quality=4)

        # Second review
        state2 = SM2State(
            easiness_factor=2.5,
            interval=6,
            repetitions=2,
        )
        db.update_progress(problem_id, state2, quality=4)

        results = db.get_problems()
        _, progress = results[0]
        assert progress is not None
        assert progress.interval == 6
        assert progress.repetitions == 2
        assert progress.attempts == 2  # Incremented twice

    def test_get_due_problems(self, db_with_problems: Database):
        """Get problems that are due for review."""
        # Add progress with past due date
        results = db_with_problems.get_problems()
        problem_id = results[0][0].id

        past_due = SM2State(
            easiness_factor=2.5,
            interval=1,
            repetitions=1,
            next_review=datetime.now() - timedelta(days=1),
        )
        db_with_problems.update_progress(problem_id, past_due, quality=4)

        due = db_with_problems.get_due_problems()
        assert len(due) == 1
        assert due[0][0].id == problem_id

    def test_get_new_problems(self, db_with_problems: Database):
        """Get problems never reviewed."""
        new_problems = db_with_problems.get_new_problems()
        assert len(new_problems) == 4  # All are new

        # Review one
        results = db_with_problems.get_problems()
        problem_id = results[0][0].id
        state = SM2State(easiness_factor=2.5, interval=1, repetitions=1)
        db_with_problems.update_progress(problem_id, state, quality=4)

        new_problems = db_with_problems.get_new_problems()
        assert len(new_problems) == 3

    def test_ensure_progress_exists(
        self,
        db: Database,
        sample_problem: Problem,
    ):
        """ensure_progress_exists creates minimal progress."""
        problem_id = db.add_problem(sample_problem)
        db.ensure_progress_exists(problem_id)

        results = db.get_problems()
        _, progress = results[0]
        assert progress is not None
        assert progress.easiness_factor == 2.5  # Default


class TestNextRecommendation(TestDatabase):
    """Tests for get_next_recommendation."""

    def test_recommends_due_first(self, db_with_problems: Database):
        """Due problems are recommended before new ones."""
        # Make one problem due
        results = db_with_problems.get_problems()
        problem_id = results[0][0].id

        due_state = SM2State(
            easiness_factor=2.5,
            interval=1,
            repetitions=1,
            next_review=datetime.now() - timedelta(days=1),
        )
        db_with_problems.update_progress(problem_id, due_state, quality=4)

        recommendation = db_with_problems.get_next_recommendation()
        assert recommendation is not None
        problem, progress = recommendation
        assert problem.id == problem_id
        assert progress is not None

    def test_recommends_new_when_no_due(self, db_with_problems: Database):
        """New problems are recommended when none are due."""
        recommendation = db_with_problems.get_next_recommendation()
        assert recommendation is not None
        _problem, progress = recommendation
        assert progress is None  # New problem

    def test_recommends_hardest_when_all_reviewed(
        self,
        db_with_problems: Database,
    ):
        """Hardest (lowest EF) recommended when all reviewed."""
        # Review all problems with future dates
        results = db_with_problems.get_problems()
        for problem, _ in results:
            future = datetime.now() + timedelta(days=30)
            # Use different EFs
            ef = 2.5 if problem.title != "3Sum" else 1.5  # 3Sum is hardest
            state = SM2State(
                easiness_factor=ef,
                interval=30,
                repetitions=5,
                next_review=future,
            )
            db_with_problems.update_progress(problem.id, state, quality=4)

        recommendation = db_with_problems.get_next_recommendation()
        assert recommendation is not None
        problem, _ = recommendation
        assert problem.title == "3Sum"  # Lowest EF

    def test_filter_by_difficulty(self, db_with_problems: Database):
        """Filter recommendations by difficulty."""
        recommendation = db_with_problems.get_next_recommendation(difficulty="Hard")
        assert recommendation is not None
        problem, _ = recommendation
        assert problem.difficulty == Difficulty.HARD


class TestStatistics(TestDatabase):
    """Tests for statistics operations."""

    def test_get_statistics_empty(self, db: Database):
        """Statistics for empty database."""
        stats = db.get_statistics()
        assert stats.total_problems == 0
        assert stats.reviewed_problems == 0
        assert stats.solved_problems == 0

    def test_get_statistics(self, db_with_problems: Database):
        """Statistics with problems."""
        stats = db_with_problems.get_statistics()
        assert stats.total_problems == 4
        assert stats.easy_total == 2
        assert stats.medium_total == 1
        assert stats.hard_total == 1

    def test_get_categories(self, db_with_problems: Database):
        """Get unique categories."""
        categories = db_with_problems.get_categories()
        assert "Arrays & Hashing" in categories
        assert "Two Pointers" in categories
        assert "Linked List" in categories

    def test_get_problem_sets(self, db_with_problems: Database):
        """Get unique problem sets."""
        sets = db_with_problems.get_problem_sets()
        assert "blind75" in sets


class TestStreaks(TestDatabase):
    """Tests for streak calculation."""

    def test_current_streak_no_sessions(self, db: Database):
        """No sessions means no streak."""
        stats = db.get_statistics()
        assert stats.current_streak == 0

    def test_current_streak_with_review(
        self,
        db: Database,
        sample_problem: Problem,
    ):
        """Reviewing today starts a streak."""
        problem_id = db.add_problem(sample_problem)
        state = SM2State(easiness_factor=2.5, interval=1, repetitions=1)
        db.update_progress(problem_id, state, quality=4)

        stats = db.get_statistics()
        assert stats.current_streak == 1
