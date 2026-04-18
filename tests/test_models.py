"""Tests for Pydantic models.

These tests verify that the data models work correctly with
validation, serialization, and computed properties.
"""

from datetime import datetime, timedelta

import pytest

from dsap.models import (
    Config,
    Difficulty,
    Problem,
    ProblemProgress,
    ReviewSession,
    Statistics,
)

# Helpers ---------------------------------------------------------------------


def make_problem(**overrides: object) -> Problem:
    """Create a Problem with default values, allowing overrides."""
    base: dict[str, object] = {
        "title": "Two Sum",
        "url": "https://leetcode.com/problems/two-sum/",
        "difficulty": Difficulty.EASY,
        "category": "Arrays & Hashing",
    }
    base.update(overrides)
    return Problem(**base)


def make_progress(**overrides: object) -> ProblemProgress:
    """Create a ProblemProgress with default values, allowing overrides."""
    base: dict[str, object] = {"problem_id": 1}
    base.update(overrides)
    return ProblemProgress(**base)


# Difficulty ------------------------------------------------------------------


class TestDifficulty:
    def test_difficulty_values(self) -> None:
        assert Difficulty.EASY.value == "Easy"
        assert Difficulty.MEDIUM.value == "Medium"
        assert Difficulty.HARD.value == "Hard"

    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            ("Easy", Difficulty.EASY),
            ("Medium", Difficulty.MEDIUM),
            ("Hard", Difficulty.HARD),
            ("easy", Difficulty.EASY),
            ("MEDIUM", Difficulty.MEDIUM),
            ("  hard  ", Difficulty.HARD),
        ],
    )
    def test_from_string_valid_variants(self, value: str, expected: Difficulty) -> None:
        assert Difficulty.from_string(value) == expected

    def test_from_string_invalid(self) -> None:
        with pytest.raises(ValueError, match="Invalid difficulty"):
            Difficulty.from_string("Invalid")
        with pytest.raises(ValueError):
            Difficulty.from_string("")


# Problem ---------------------------------------------------------------------


class TestProblem:
    def test_valid_problem(self) -> None:
        problem = make_problem(
            description="Find two numbers that sum to target",
            tags=["array", "hash-table"],
            problem_set="blind75",
            problem_number=1,
        )
        assert problem.title == "Two Sum"
        assert problem.difficulty == Difficulty.EASY
        assert problem.category == "Arrays & Hashing"
        assert "array" in problem.tags

    def test_minimal_problem_defaults(self) -> None:
        problem = make_problem()
        assert problem.id is None
        assert problem.description == ""
        assert problem.tags == []
        assert problem.problem_set == "custom"
        assert problem.problem_number == 0
        assert problem.company_tags == []
        assert problem.hints == []
        assert problem.created_at is None

    def test_title_whitespace_stripped(self) -> None:
        problem = make_problem(title="  Two Sum  ")
        assert problem.title == "Two Sum"

    def test_category_whitespace_stripped(self) -> None:
        problem = make_problem(category="  Arrays & Hashing  ")
        assert problem.category == "Arrays & Hashing"

    def test_difficulty_from_string(self) -> None:
        problem = make_problem(difficulty="easy")
        assert problem.difficulty == Difficulty.EASY

    def test_tags_from_comma_string(self) -> None:
        problem = make_problem(
            tags="array, hash-table, two-pointers",
        )
        assert problem.tags == ["array", "hash-table", "two-pointers"]

    def test_tags_none_becomes_empty_list(self) -> None:
        problem = make_problem(tags=None)
        assert problem.tags == []

    def test_invalid_url(self) -> None:
        with pytest.raises(ValueError):
            make_problem(url="not-a-valid-url")

    def test_empty_title_invalid(self) -> None:
        with pytest.raises(ValueError):
            make_problem(title="")

    def test_title_too_long_invalid(self) -> None:
        with pytest.raises(ValueError):
            make_problem(title="A" * 201)

    def test_validate_assignment(self) -> None:
        problem = make_problem()
        with pytest.raises(ValueError):
            problem.title = ""

        problem.title = "Valid"
        assert problem.title == "Valid"


# ProblemProgress -------------------------------------------------------------


class TestProblemProgress:
    def test_default_values(self) -> None:
        progress = make_progress()
        assert progress.easiness_factor == 2.5
        assert progress.interval == 0
        assert progress.repetitions == 0
        assert progress.next_review is None
        assert progress.last_reviewed is None
        assert progress.attempts == 0
        assert progress.solved is False

    def test_is_new(self) -> None:
        new_progress = make_progress()
        assert new_progress.is_new() is True

        reviewed = make_progress(attempts=1)
        assert reviewed.is_new() is False

    def test_is_due_no_review_date(self) -> None:
        progress = make_progress()
        assert progress.is_due() is True

    def test_is_due_past_date(self) -> None:
        now = datetime.now()
        yesterday = now - timedelta(days=1)
        progress = make_progress(next_review=yesterday)
        assert progress.is_due(now=now) is True

    def test_is_due_future_date(self) -> None:
        now = datetime.now()
        tomorrow = now + timedelta(days=1)
        progress = make_progress(next_review=tomorrow)
        assert progress.is_due(now=now) is False

    def test_easiness_factor_minimum(self) -> None:
        with pytest.raises(ValueError):
            make_progress(easiness_factor=1.0)

    def test_easiness_factor_maximum(self) -> None:
        with pytest.raises(ValueError):
            make_progress(easiness_factor=6.0)

    def test_quality_range(self) -> None:
        valid = make_progress(last_quality=5)
        assert valid.last_quality == 5

        with pytest.raises(ValueError):
            make_progress(last_quality=6)
        with pytest.raises(ValueError):
            make_progress(last_quality=-1)

    def test_solved_date_validation(self) -> None:
        first = datetime.now()
        before_first = first - timedelta(days=1)

        with pytest.raises(ValueError, match="solved_at cannot be before"):
            make_progress(
                first_attempted=first,
                solved_at=before_first,
                solved=True,
            )

    def test_solved_sets_solved_at(self) -> None:
        progress = make_progress(solved=True)
        assert progress.solved_at is not None

    def test_validate_assignment_enforced(self) -> None:
        progress = make_progress()
        with pytest.raises(ValueError):
            progress.easiness_factor = 1.0


# ReviewSession ---------------------------------------------------------------


class TestReviewSession:
    def test_default_values(self) -> None:
        session = ReviewSession()
        assert session.id is None
        assert session.problems_reviewed == 0
        assert session.average_quality == 0.0
        assert session.date is not None

    def test_quality_bounds(self) -> None:
        with pytest.raises(ValueError):
            ReviewSession(average_quality=5.5)
        with pytest.raises(ValueError):
            ReviewSession(average_quality=-0.1)

    def test_non_negative_counts(self) -> None:
        with pytest.raises(ValueError):
            ReviewSession(problems_reviewed=-1)
        with pytest.raises(ValueError):
            ReviewSession(duration_minutes=-5)


# Statistics ------------------------------------------------------------------


class TestStatistics:
    def test_default_values(self) -> None:
        stats = Statistics()
        assert stats.total_problems == 0
        assert stats.solved_problems == 0
        assert stats.current_streak == 0

    def test_solved_percentage_empty(self) -> None:
        stats = Statistics(total_problems=0)
        assert stats.solved_percentage == 0.0

    def test_solved_percentage_calculation(self) -> None:
        stats = Statistics(total_problems=100, solved_problems=75)
        assert stats.solved_percentage == 75.0

    def test_difficulty_percentages(self) -> None:
        stats = Statistics(
            easy_total=20,
            easy_solved=15,
            medium_total=50,
            medium_solved=25,
            hard_total=30,
            hard_solved=6,
        )
        assert stats.easy_percentage == 75.0
        assert stats.medium_percentage == 50.0
        assert stats.hard_percentage == 20.0

    def test_difficulty_percentage_zero_total(self) -> None:
        stats = Statistics(easy_total=0)
        assert stats.easy_percentage == 0.0


# Config ----------------------------------------------------------------------


class TestConfig:
    def test_default_values(self) -> None:
        config = Config()
        assert config.daily_goal == 5
        assert config.preferred_difficulty is None
        assert config.show_hints is True
        assert config.auto_open_browser is True
        assert config.theme == "default"

    def test_daily_goal_bounds(self) -> None:
        with pytest.raises(ValueError):
            Config(daily_goal=0)
        with pytest.raises(ValueError):
            Config(daily_goal=101)

        valid = Config(daily_goal=50)
        assert valid.daily_goal == 50

    def test_preferred_difficulty(self) -> None:
        config = Config(preferred_difficulty=Difficulty.MEDIUM)
        assert config.preferred_difficulty == Difficulty.MEDIUM
