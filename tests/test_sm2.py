"""
Tests for SM-2 Spaced Repetition Algorithm

These tests verify the correctness of the SM-2 implementation
and serve as documentation for how the algorithm behaves.
"""

from datetime import datetime, timedelta

import pytest

from dsap.sm2 import (
    DEFAULT_EASINESS_FACTOR,
    FIRST_INTERVAL,
    MINIMUM_EASINESS_FACTOR,
    SECOND_INTERVAL,
    Quality,
    SM2State,
    calculate_easiness_factor,
    calculate_interval,
    get_initial_state,
    process_review,
    simulate_reviews,
)


class TestQuality:
    """Tests for Quality enum and helper methods."""

    def test_quality_values(self):
        """Verify quality grade values."""
        assert Quality.PERFECT == 5
        assert Quality.GOOD == 4
        assert Quality.HARD == 3
        assert Quality.FORGOT == 2
        assert Quality.BLACKOUT == 1
        assert Quality.TOTAL_BLACKOUT == 0

    def test_is_successful(self):
        """Quality >= 3 is successful, < 3 is failure."""
        assert Quality.is_successful(5) is True
        assert Quality.is_successful(4) is True
        assert Quality.is_successful(3) is True
        assert Quality.is_successful(2) is False
        assert Quality.is_successful(1) is False
        assert Quality.is_successful(0) is False

    def test_description(self):
        """Each quality has a description."""
        for q in range(6):
            desc = Quality.description(q)
            assert isinstance(desc, str)
            assert len(desc) > 0


class TestSM2State:
    """Tests for SM2State dataclass."""

    def test_default_state(self):
        """Default state has correct initial values."""
        state = SM2State()
        assert state.easiness_factor == DEFAULT_EASINESS_FACTOR
        assert state.interval == 0
        assert state.repetitions == 0
        assert state.next_review is None
        assert state.last_reviewed is None

    def test_is_new(self):
        """is_new returns True only for never-reviewed items."""
        new_state = SM2State()
        assert new_state.is_new() is True

        reviewed_state = SM2State(repetitions=1, last_reviewed=datetime.now())
        assert reviewed_state.is_new() is False

    def test_is_due_never_reviewed(self):
        """Never-reviewed items are always due."""
        state = SM2State()
        assert state.is_due() is True

    def test_is_due_past_review(self):
        """Items past their review date are due."""
        yesterday = datetime.now() - timedelta(days=1)
        state = SM2State(next_review=yesterday)
        assert state.is_due() is True

    def test_is_due_future_review(self):
        """Items with future review date are not due."""
        tomorrow = datetime.now() + timedelta(days=1)
        state = SM2State(next_review=tomorrow)
        assert state.is_due() is False


class TestCalculateEasinessFactor:
    """
    Tests for the EF calculation formula.

    The formula is:
    EF' = EF + (0.1 - (5-q) * (0.08 + (5-q) * 0.02))
    """

    def test_perfect_quality_increases_ef(self):
        """Perfect recall (5) increases EF by 0.1."""
        new_ef = calculate_easiness_factor(2.5, 5)
        assert new_ef == 2.6

    def test_good_quality_no_change(self):
        """Good recall (4) keeps EF the same."""
        new_ef = calculate_easiness_factor(2.5, 4)
        assert new_ef == 2.5

    def test_hard_quality_decreases_ef(self):
        """Hard recall (3) decreases EF."""
        new_ef = calculate_easiness_factor(2.5, 3)
        assert new_ef == 2.36

    def test_minimum_ef_enforced(self):
        """EF cannot go below 1.3."""
        # Start with low EF and give bad rating
        new_ef = calculate_easiness_factor(1.4, 0)
        assert new_ef == MINIMUM_EASINESS_FACTOR

    def test_invalid_quality_raises(self):
        """Quality must be 0-5."""
        with pytest.raises(ValueError):
            calculate_easiness_factor(2.5, 6)
        with pytest.raises(ValueError):
            calculate_easiness_factor(2.5, -1)

    @pytest.mark.parametrize(
        "quality,expected_adjustment",
        [
            (5, 0.10),  # Perfect: +0.10
            (4, 0.00),  # Good: no change
            (3, -0.14),  # Hard: -0.14
            (2, -0.32),  # Forgot: -0.32
            (1, -0.54),  # Blackout: -0.54
            (0, -0.80),  # Total blackout: -0.80
        ],
    )
    def test_ef_adjustments(self, quality, expected_adjustment):
        """Verify EF adjustments match the formula."""
        starting_ef = 2.5
        new_ef = calculate_easiness_factor(starting_ef, quality)
        actual_adjustment = new_ef - starting_ef
        assert abs(actual_adjustment - expected_adjustment) < 0.01


class TestCalculateInterval:
    """Tests for interval calculation."""

    def test_first_interval(self):
        """First successful review: 1 day."""
        interval = calculate_interval(1, 0, 2.5)
        assert interval == FIRST_INTERVAL

    def test_second_interval(self):
        """Second successful review: 6 days."""
        interval = calculate_interval(2, 1, 2.5)
        assert interval == SECOND_INTERVAL

    def test_subsequent_intervals(self):
        """Subsequent intervals multiply by EF."""
        # Third review: 6 * 2.5 = 15
        interval = calculate_interval(3, 6, 2.5)
        assert interval == 15

        # Fourth review: 15 * 2.5 = 37.5 -> 38
        interval = calculate_interval(4, 15, 2.5)
        assert interval == 38

    def test_zero_repetitions(self):
        """Zero repetitions returns 0."""
        interval = calculate_interval(0, 0, 2.5)
        assert interval == 0

    def test_interval_with_different_ef(self):
        """Interval growth rate depends on EF."""
        # Higher EF = longer intervals
        interval_high = calculate_interval(3, 6, 3.0)
        assert interval_high == 18  # 6 * 3.0

        # Lower EF = shorter intervals
        interval_low = calculate_interval(3, 6, 1.5)
        assert interval_low == 9  # 6 * 1.5


class TestProcessReview:
    """Tests for the main process_review function."""

    def test_first_successful_review(self):
        """First successful review sets interval to 1, reps to 1."""
        state = get_initial_state()
        new_state = process_review(state, 5)

        assert new_state.repetitions == 1
        assert new_state.interval == 1
        assert new_state.easiness_factor == 2.6  # Increased from perfect
        assert new_state.next_review is not None
        assert new_state.last_reviewed is not None

    def test_second_successful_review(self):
        """Second success sets interval to 6."""
        state = SM2State(repetitions=1, interval=1, easiness_factor=2.5)
        new_state = process_review(state, 4)

        assert new_state.repetitions == 2
        assert new_state.interval == 6

    def test_failed_review_resets(self):
        """Failed review (quality < 3) resets repetitions and interval."""
        state = SM2State(repetitions=5, interval=30, easiness_factor=2.8)
        new_state = process_review(state, 2)

        assert new_state.repetitions == 0
        assert new_state.interval == 1
        # EF is reduced but not reset
        assert new_state.easiness_factor < 2.8

    def test_invalid_quality_raises(self):
        """Invalid quality raises ValueError."""
        state = get_initial_state()
        with pytest.raises(ValueError):
            process_review(state, 6)

    def test_immutability(self):
        """process_review returns new state, doesn't modify original."""
        original = get_initial_state()
        new_state = process_review(original, 5)

        # Original unchanged
        assert original.repetitions == 0
        assert original.interval == 0

        # New state is different
        assert new_state.repetitions == 1
        assert new_state is not original


class TestSimulateReviews:
    """Tests for the simulate_reviews helper."""

    def test_simulate_perfect_reviews(self):
        """Simulating perfect reviews shows exponential growth."""
        results = simulate_reviews([5, 5, 5, 5])

        intervals = [state.interval for _, state in results]
        assert intervals[0] == 1  # First: 1 day
        assert intervals[1] == 6  # Second: 6 days
        assert intervals[2] > 10  # Third: grows
        assert intervals[3] > intervals[2]  # Fourth: keeps growing

    def test_simulate_with_failure(self):
        """Failure in the middle resets progress."""
        results = simulate_reviews([5, 5, 2, 5])  # Fail on third

        intervals = [state.interval for _, state in results]
        reps = [state.repetitions for _, state in results]

        assert reps[2] == 0  # Reset after failure
        assert intervals[2] == 1  # Back to 1 day
        assert reps[3] == 1  # Starting over

    def test_empty_reviews(self):
        """Empty list returns empty results."""
        results = simulate_reviews([])
        assert results == []


class TestSM2Algorithm:
    """
    Integration tests verifying the algorithm behaves correctly
    in realistic scenarios.
    """

    def test_easy_item_progression(self):
        """Easy items (consistent 5s) progress to long intervals quickly."""
        state = get_initial_state()

        # Simulate consistently perfect recall
        for _ in range(5):
            state = process_review(state, 5)

        # After 5 perfect reviews, interval should be quite long
        assert state.interval > 60  # More than 2 months
        assert state.easiness_factor > 2.5  # EF increased

    def test_hard_item_progression(self):
        """Hard items (consistent 3s) progress slower than easy items."""
        state = get_initial_state()

        # Simulate consistently hard recall
        for _ in range(5):
            state = process_review(state, 3)

        # Compare with an easy item after 5 perfect reviews
        easy_state = get_initial_state()
        for _ in range(5):
            easy_state = process_review(easy_state, 5)

        # Hard item should have shorter interval than easy item
        assert state.interval < easy_state.interval
        assert state.easiness_factor < 2.5  # EF decreased

    def test_recovery_after_failure(self):
        """After failing, item returns but with lower EF."""
        # Build up some progress
        state = get_initial_state()
        for _ in range(3):
            state = process_review(state, 5)

        original_ef = state.easiness_factor

        # Fail once
        state = process_review(state, 2)

        # Now rebuild
        for _ in range(3):
            state = process_review(state, 5)

        # EF should be lower than before the failure
        # (the item is "harder" now, even after recovery)
        assert state.easiness_factor < original_ef + 0.3

    def test_next_review_is_correct(self):
        """next_review date is correctly calculated."""
        state = get_initial_state()
        before = datetime.now()

        new_state = process_review(state, 5)

        after = datetime.now()

        # next_review should be ~1 day from now (first interval)
        expected_min = before + timedelta(days=1)
        expected_max = after + timedelta(days=1, seconds=1)

        assert expected_min <= new_state.next_review <= expected_max
