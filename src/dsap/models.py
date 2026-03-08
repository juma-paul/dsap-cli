"""Pydantic models for DSAP.

These models define the core data structures used throughout the application.
Using Pydantic provides:
- Automatic validation of data types and constraints
- Clear documentation of fields and their requirements
- Easy serialization to/from JSON and dictionaries
- Type hints for better IDE support
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Annotated, Any

from pydantic import BaseModel, Field, HttpUrl, field_validator, model_validator


class DSAPBaseModel(BaseModel):
    """Base model with common configuration for all DSAP models."""

    model_config = {
        "validate_assignment": True,
    }


class Difficulty(str, Enum):
    """Problem difficulty levels.

    Using an enum ensures only valid difficulties are accepted
    and provides better autocomplete in IDEs.
    """

    EASY = "Easy"
    MEDIUM = "Medium"
    HARD = "Hard"

    @classmethod
    def from_string(cls, value: str) -> Difficulty:
        """Convert a string to Difficulty, case-insensitive."""
        normalized = value.strip().lower()
        mapping: dict[str, Difficulty] = {
            "easy": cls.EASY,
            "medium": cls.MEDIUM,
            "hard": cls.HARD,
        }
        if normalized not in mapping:
            raise ValueError(
                f"Invalid difficulty: {value}. Must be Easy, Medium, or Hard"
            )
        return mapping[normalized]


class Problem(DSAPBaseModel):
    """Represents a DSA problem from a curated problem set."""

    id: int | None = None
    title: Annotated[str, Field(min_length=1, max_length=200)]
    url: HttpUrl
    difficulty: Difficulty
    category: Annotated[str, Field(min_length=1, max_length=100)]
    description: str = ""
    tags: list[str] = Field(default_factory=list)
    problem_set: str = "custom"
    problem_number: int = Field(default=0, ge=0)
    company_tags: list[str] = Field(default_factory=list)
    hints: list[str] = Field(default_factory=list)
    created_at: datetime | None = None

    model_config = {
        "str_strip_whitespace": True,
        "validate_assignment": True,
    }

    @field_validator("title", "category")
    @classmethod
    def strip_whitespace(cls, value: str) -> str:
        """Strip leading/trailing whitespace from string fields."""
        return value.strip()

    @field_validator("tags", "company_tags", "hints", mode="before")
    @classmethod
    def ensure_list(cls, value: Any) -> list[str]:
        """Ensure list fields are actually lists of strings."""
        if value is None:
            return []
        if isinstance(value, str):
            return [x.strip() for x in value.split(",") if x.strip()]
        if isinstance(value, list):
            return value
        return [str(value)]

    @field_validator("difficulty", mode="before")
    @classmethod
    def normalize_difficulty(cls, value: Difficulty | str) -> Difficulty:
        """Accept difficulty as string or enum."""
        if isinstance(value, Difficulty):
            return value
        return Difficulty.from_string(value)


class ProblemProgress(DSAPBaseModel):
    """Tracks user's progress on a specific problem with SM-2 state."""

    problem_id: int

    # SM-2 state with validation
    easiness_factor: Annotated[float, Field(ge=1.3, le=5.0)] = 2.5
    interval: Annotated[int, Field(ge=0)] = 0
    repetitions: Annotated[int, Field(ge=0)] = 0
    next_review: datetime | None = None
    last_reviewed: datetime | None = None

    # Practice tracking
    attempts: Annotated[int, Field(ge=0)] = 0
    solved: bool = False
    first_attempted: datetime | None = None
    solved_at: datetime | None = None
    last_quality: Annotated[int, Field(ge=0, le=5)] | None = None
    notes: str = ""
    time_spent_minutes: Annotated[int, Field(ge=0)] = 0

    @model_validator(mode="after")
    def validate_dates(self) -> ProblemProgress:
        """Ensure date fields are logically consistent."""
        if (
            self.solved_at
            and self.first_attempted
            and self.solved_at < self.first_attempted
        ):
            raise ValueError("solved_at cannot be before first_attempted")

        if self.solved and self.solved_at is None:
            self.solved_at = datetime.now()
        return self

    def is_due(self, now: datetime | None = None) -> bool:
        """Check if this problem is due for review."""
        if now is None:
            now = datetime.now()
        if self.next_review is None:
            return True
        return now >= self.next_review

    def is_new(self) -> bool:
        """Check if this problem has never been attempted."""
        return self.attempts == 0


class ReviewSession(DSAPBaseModel):
    """Represents a single practice/review session."""

    id: int | None = None
    date: datetime = Field(default_factory=datetime.now)
    problems_reviewed: Annotated[int, Field(ge=0)] = 0
    problems_due: Annotated[int, Field(ge=0)] = 0
    average_quality: Annotated[float, Field(ge=0, le=5)] = 0.0
    duration_minutes: Annotated[int, Field(ge=0)] = 0
    notes: str = ""


class Statistics(DSAPBaseModel):
    """Aggregated statistics for display."""

    total_problems: int = 0
    reviewed_problems: int = 0
    solved_problems: int = 0
    due_today: int = 0
    due_this_week: int = 0
    average_easiness_factor: float = 2.5
    current_streak: int = 0
    best_streak: int = 0
    total_reviews: int = 0

    # Breakdown by difficulty
    easy_total: int = 0
    easy_solved: int = 0
    medium_total: int = 0
    medium_solved: int = 0
    hard_total: int = 0
    hard_solved: int = 0

    @property
    def solved_percentage(self) -> float:
        """Calculate overall solved percentage."""
        if self.total_problems == 0:
            return 0.0
        return round(self.solved_problems / self.total_problems * 100, 1)

    @property
    def easy_percentage(self) -> float:
        """Calculate Easy solved percentage."""
        if self.easy_total == 0:
            return 0.0
        return round(self.easy_solved / self.easy_total * 100, 1)

    @property
    def medium_percentage(self) -> float:
        """Calculate Medium solved percentage."""
        if self.medium_total == 0:
            return 0.0
        return round(self.medium_solved / self.medium_total * 100, 1)

    @property
    def hard_percentage(self) -> float:
        """Calculate Hard solved percentage."""
        if self.hard_total == 0:
            return 0.0
        return round(self.hard_solved / self.hard_total * 100, 1)


class Config(DSAPBaseModel):
    """User configuration settings.

    Stored in ~/.dsap/config.json
    """

    daily_goal: Annotated[int, Field(ge=1, le=100)] = 5
    preferred_difficulty: Difficulty | None = None
    preferred_set: str | None = None
    favorite_categories: list[str] = Field(default_factory=list)
    show_hints: bool = True
    auto_open_browser: bool = True
    theme: str = "default"
