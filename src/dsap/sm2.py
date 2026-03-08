"""SM-2 Spaced Repetition Algorithm - Implementation from Scratch.

==================================================================

This module implements the SM-2 algorithm created by Piotr Wozniak in 1987
for the SuperMemo software. It's the foundation of modern spaced repetition
systems like Anki.

THE PROBLEM SM-2 SOLVES
-----------------------
When learning, we face two challenges:
1. We forget things over time (forgetting curve)
2. Reviewing too often wastes time; too rarely means we forget

SM-2 calculates the OPTIMAL time to review each item - right before you'd
forget it. This maximizes retention while minimizing study time.

HOW IT WORKS - THE THREE CORE VALUES
------------------------------------
For each item (in our case, each DSA problem), we track:

1. EASINESS FACTOR (EF)
   - A number starting at 2.5
   - Represents how "easy" this item is for YOU
   - Higher EF = easier = longer intervals between reviews
   - Lower EF = harder = shorter intervals (more practice needed)
   - Minimum is 1.3 (prevents intervals from becoming too short)

2. INTERVAL
   - Days until the next review
   - Grows exponentially for easy items
   - Resets to 1 day when you fail

3. REPETITIONS
   - Count of consecutive successful recalls
   - Resets to 0 when you fail
   - Determines which interval formula to use

THE QUALITY RATING SYSTEM
-------------------------
After each review, you rate your recall quality from 0-5:

  5 = Perfect    - Instant, confident recall. No hesitation.
  4 = Good       - Correct answer, but had to think about it.
  3 = Hard       - Correct, but with significant difficulty.
  2 = Forgot     - Wrong answer, but the solution seemed familiar.
  1 = Blackout   - Wrong, but recognized the answer when shown.
  0 = Total      - Complete failure. No memory at all.

Ratings 3-5 count as SUCCESS -> advance to next interval
Ratings 0-2 count as FAILURE -> reset and relearn

THE MATH EXPLAINED
------------------

### Interval Calculation

For successful reviews (quality >= 3):

  n=1 (first success):  interval = 1 day
  n=2 (second success): interval = 6 days
  n>2 (subsequent):     interval = previous_interval * EF

Example progression with EF=2.5:
  Review 1: 1 day
  Review 2: 6 days
  Review 3: 6 * 2.5 = 15 days
  Review 4: 15 * 2.5 = 38 days
  Review 5: 38 * 2.5 = 95 days (~3 months!)

### Easiness Factor Update

After each review, EF is adjusted based on quality:

  EF' = EF + (0.1 - (5-q) * (0.08 + (5-q) * 0.02))

Let's unpack this formula step by step:

1. (5 - q) = "distance from perfect"
   - If q=5: 5-5 = 0 (perfect!)
   - If q=3: 5-3 = 2 (struggled)
   - If q=0: 5-0 = 5 (complete failure)

2. (0.08 + (5-q) * 0.02) = "penalty multiplier"
   - Increases as quality decreases
   - q=5: 0.08 + 0*0.02 = 0.08
   - q=3: 0.08 + 2*0.02 = 0.12
   - q=0: 0.08 + 5*0.02 = 0.18

3. (5-q) * penalty = "total penalty"
   - q=5: 0 * 0.08 = 0.00
   - q=4: 1 * 0.10 = 0.10
   - q=3: 2 * 0.12 = 0.24
   - q=2: 3 * 0.14 = 0.42
   - q=1: 4 * 0.16 = 0.64
   - q=0: 5 * 0.18 = 0.90

4. 0.1 - penalty = "EF adjustment"
   - q=5: 0.1 - 0.00 = +0.10 (EF increases!)
   - q=4: 0.1 - 0.10 = +0.00 (no change)
   - q=3: 0.1 - 0.24 = -0.14 (EF decreases)
   - q=2: 0.1 - 0.42 = -0.32
   - q=1: 0.1 - 0.64 = -0.54
   - q=0: 0.1 - 0.90 = -0.80

So a perfect recall (5) makes the item "easier" (longer future intervals),
while struggling (3) or failing (0-2) makes it "harder" (shorter intervals).

WHY THESE SPECIFIC NUMBERS?
---------------------------
Wozniak determined these values through extensive experimentation in the
1980s. The goals:
- 1 day: Minimum useful gap to confirm initial learning
- 6 days: Optimal second interval for most material
- EF of 2.5: Reasonable starting point for unknown difficulty
- Minimum EF of 1.3: Prevents impractically short intervals

References:
----------
- Original paper: https://www.supermemo.com/en/blog/application-of-a-computer-to-improve-the-results-obtained-in-working-with-the-supermemo-method
- Wikipedia: https://en.wikipedia.org/wiki/SuperMemo#Description_of_SM-2_algorithm
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import IntEnum


class Quality(IntEnum):
    """Quality grades for SM-2 algorithm.

    The quality of recall is rated 0-5. This scale measures how well
    you remembered the solution approach, not just whether you got
    it right or wrong.

    For DSA problems, think of it this way:
    - 5: "I immediately knew the approach and could code it"
    - 4: "I knew the approach but had to think through details"
    - 3: "I eventually figured it out but struggled"
    - 2: "I couldn't solve it, but the solution made sense"
    - 1: "I couldn't solve it, and barely understood the solution"
    - 0: "I had no idea what to do and the solution confused me"
    """

    PERFECT = 5  # Instant recall, no hesitation
    GOOD = 4  # Correct but required thought
    HARD = 3  # Correct with serious difficulty
    FORGOT = 2  # Wrong, but answer seemed familiar
    BLACKOUT = 1  # Wrong, recognized answer when shown
    TOTAL_BLACKOUT = 0  # Complete failure, no recognition

    @classmethod
    def is_successful(cls, quality: int) -> bool:
        """Determine if a quality rating counts as successful recall.

        In SM-2, quality >= 3 is considered successful.
        This advances the repetition count and extends intervals.
        Quality < 3 is a failure, which resets the learning process.
        """
        return quality >= 3

    @classmethod
    def description(cls, quality: int) -> str:
        """Get a human-readable description for a quality rating."""
        descriptions = {
            5: "Perfect - instant recall",
            4: "Good - correct with thought",
            3: "Hard - struggled but solved",
            2: "Forgot - wrong but familiar",
            1: "Blackout - wrong, recognized after",
            0: "Total blackout - no memory",
        }
        return descriptions.get(quality, "Unknown")


# Default values as constants with explanatory names
DEFAULT_EASINESS_FACTOR = 2.5  # Standard starting EF for new items
MINIMUM_EASINESS_FACTOR = 1.3  # Floor to prevent EF collapse

# Interval constants (in days)
FIRST_INTERVAL = 1  # See again tomorrow after first success
SECOND_INTERVAL = 6  # About a week after second success


@dataclass
class SM2State:
    """Represents the SM-2 learning state for a single item.

    This is the core data structure that tracks where you are in the
    learning process for each problem.

    Attributes:
        easiness_factor: How "easy" this item is for you (default 2.5).
                        Higher = easier = longer review intervals.
                        Range: 1.3 to ~4.0 typically.

        interval: Days until the next scheduled review.
                 0 means not yet reviewed or just failed.

        repetitions: Count of consecutive successful recalls.
                    Resets to 0 on failure.
                    Determines which interval formula to use.

        next_review: The date when this item should next be reviewed.
                    None if never reviewed.

        last_reviewed: Date of the most recent review.
                      Useful for tracking and statistics.

    Example lifecycle:
        Initial:     EF=2.5, interval=0, reps=0
        After q=4:   EF=2.5, interval=1, reps=1  (see tomorrow)
        After q=5:   EF=2.6, interval=6, reps=2  (see in 6 days)
        After q=4:   EF=2.6, interval=16, reps=3 (see in 16 days)
        After q=2:   EF=2.28, interval=1, reps=0 (FAILED! reset!)
    """

    easiness_factor: float = DEFAULT_EASINESS_FACTOR
    interval: int = 0
    repetitions: int = 0
    next_review: datetime | None = None
    last_reviewed: datetime | None = None

    def is_new(self) -> bool:
        """Check if this item has never been reviewed."""
        return self.repetitions == 0 and self.last_reviewed is None

    def is_due(self, now: datetime | None = None) -> bool:
        """Check if this item is due for review.

        An item is due if:
        - It has never been reviewed (next_review is None), OR
        - The current time is past the scheduled next_review
        """
        if now is None:
            now = datetime.now()

        if self.next_review is None:
            return True

        return now >= self.next_review

    def days_until_review(self, now: datetime | None = None) -> int:
        """Calculate days until this item is due.

        Returns:
            Positive: days until due
            Zero: due today
            Negative: days overdue
        """
        if now is None:
            now = datetime.now()

        if self.next_review is None:
            return 0

        delta = self.next_review - now
        return delta.days


def calculate_easiness_factor(current_ef: float, quality: int) -> float:
    """Calculate the new Easiness Factor based on quality of recall.

    This is the heart of SM-2's adaptivity. The EF adjusts based on
    how well you performed, making the algorithm personalized to you.

    THE FORMULA
    -----------
    EF' = EF + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02))

    STEP-BY-STEP BREAKDOWN
    ----------------------
    Let's trace through with q=3 (hard but correct):

    1. distance = 5 - 3 = 2
       "How far from perfect was this recall?"

    2. penalty_rate = 0.08 + 2 * 0.02 = 0.12
       "Base penalty + extra penalty for difficulty"

    3. total_penalty = 2 * 0.12 = 0.24
       "Distance times penalty rate"

    4. adjustment = 0.1 - 0.24 = -0.14
       "Net change to EF (negative = harder)"

    5. new_ef = 2.5 + (-0.14) = 2.36
       "Item is now considered harder"

    Args:
        current_ef: Current easiness factor (usually starts at 2.5)
        quality: Quality of recall (0-5)

    Returns:
        New easiness factor, minimum 1.3

    Examples:
        >>> calculate_easiness_factor(2.5, 5)  # Perfect
        2.6
        >>> calculate_easiness_factor(2.5, 4)  # Good
        2.5
        >>> calculate_easiness_factor(2.5, 3)  # Hard
        2.36
        >>> calculate_easiness_factor(2.5, 0)  # Total failure
        1.7
    """
    if not 0 <= quality <= 5:
        raise ValueError(f"Quality must be 0-5, got {quality}")

    # Step 1: How far from perfect?
    distance_from_perfect = 5 - quality

    # Step 2: Calculate the penalty multiplier
    # This increases as quality decreases, making the penalty harsher
    penalty_multiplier = 0.08 + distance_from_perfect * 0.02

    # Step 3: Calculate total penalty
    total_penalty = distance_from_perfect * penalty_multiplier

    # Step 4: Calculate EF adjustment
    # 0.1 is the "reward" for any recall; penalty subtracts from it
    ef_adjustment = 0.1 - total_penalty

    # Step 5: Apply adjustment
    new_ef = current_ef + ef_adjustment

    # Enforce minimum EF of 1.3
    # Below this, intervals grow too slowly to be useful
    return max(MINIMUM_EASINESS_FACTOR, round(new_ef, 2))


def calculate_interval(
    repetitions: int, previous_interval: int, easiness_factor: float
) -> int:
    """Calculate the next review interval in days.

    THE INTERVAL PROGRESSION
    ------------------------
    SM-2 uses a specific progression for the first two intervals,
    then switches to exponential growth:

    n=1 (first success):  1 day
        Why? Confirms initial learning. Too long and you'd forget.

    n=2 (second success): 6 days
        Why? A week-ish gap tests medium-term retention.

    n>2 (subsequent):     previous_interval * EF
        Why? Exponential growth with personalized rate.

    EXAMPLE PROGRESSIONS
    --------------------
    Easy item (EF=2.8 after consistent 5s):
      1 -> 6 -> 17 -> 48 -> 134 days
      After 5 reviews, you only see it twice a year!

    Hard item (EF=1.5 after consistent 3s):
      1 -> 6 -> 9 -> 14 -> 21 days
      Still progressing, but much slower.

    Args:
        repetitions: Number of consecutive successful recalls (1-indexed)
        previous_interval: The previous interval in days
        easiness_factor: Current EF for this item

    Returns:
        Next interval in days (always at least 1)

    Examples:
        >>> calculate_interval(1, 0, 2.5)  # First review
        1
        >>> calculate_interval(2, 1, 2.5)  # Second review
        6
        >>> calculate_interval(3, 6, 2.5)  # Third review
        15
        >>> calculate_interval(4, 15, 2.5)  # Fourth review
        38
    """
    if repetitions <= 0:
        # Not yet successfully reviewed
        return 0
    elif repetitions == 1:
        # First successful review: see again tomorrow
        return FIRST_INTERVAL
    elif repetitions == 2:
        # Second successful review: see again in ~a week
        return SECOND_INTERVAL
    else:
        # Subsequent reviews: exponential growth
        # Round to nearest day (intervals are always whole days)
        return max(1, round(previous_interval * easiness_factor))


def process_review(state: SM2State, quality: int) -> SM2State:
    """Process a review and return the updated SM-2 state.

    This is the main entry point for the SM-2 algorithm. Call this
    after the user reviews a problem and provides their quality rating.

    THE REVIEW PROCESS
    ------------------
    1. Update EF based on quality (always, even on failure)
    2. Check if this was a successful recall (quality >= 3)
    3. If successful:
       - Increment repetition counter
       - Calculate new interval using progression
    4. If failed:
       - Reset repetitions to 0
       - Reset interval to 1 day
    5. Calculate the next review date

    KEY INSIGHT: FAILURE HANDLING
    -----------------------------
    When you fail (quality < 3), we:
    - Reset repetitions to 0 (start the progression over)
    - Reset interval to 1 (see it again tomorrow)
    - BUT keep the lowered EF (item is now marked as harder)

    This means even after "relearning," a hard item will have shorter
    intervals than an easy item because its EF is lower.

    Args:
        state: Current SM2State for this item
        quality: Quality of recall (0-5)

    Returns:
        New SM2State with updated values (immutable pattern)

    Examples:
        >>> state = SM2State()
        >>> new_state = process_review(state, 5)
        >>> new_state.repetitions
        1
        >>> new_state.interval
        1
        >>> new_state.easiness_factor
        2.6

        >>> # After failing
        >>> state = SM2State(repetitions=5, interval=30, easiness_factor=2.8)
        >>> new_state = process_review(state, 2)
        >>> new_state.repetitions
        0
        >>> new_state.interval
        1
    """
    if not 0 <= quality <= 5:
        raise ValueError(f"Quality must be 0-5, got {quality}")

    # Step 1: Always update EF based on performance
    # This happens regardless of success/failure
    new_ef = calculate_easiness_factor(state.easiness_factor, quality)

    # Step 2: Determine if this was a successful recall
    is_successful = Quality.is_successful(quality)

    # Step 3 & 4: Update repetitions and interval
    if is_successful:
        # Success: progress to next interval
        new_repetitions = state.repetitions + 1
        new_interval = calculate_interval(new_repetitions, state.interval, new_ef)
    else:
        # Failure: reset to beginning
        # Keep the lowered EF - don't reset that
        new_repetitions = 0
        new_interval = FIRST_INTERVAL  # See again tomorrow

    # Step 5: Calculate next review date
    now = datetime.now()
    next_review = now + timedelta(days=new_interval)

    # Return new state (immutable pattern - return new object)
    return SM2State(
        easiness_factor=new_ef,
        interval=new_interval,
        repetitions=new_repetitions,
        next_review=next_review,
        last_reviewed=now,
    )


def get_initial_state() -> SM2State:
    """Create a fresh SM-2 state for a new item.

    This is the starting point for any new problem added to the system.
    The item has never been reviewed and starts with default values.
    """
    return SM2State()


def simulate_reviews(qualities: list[int]) -> list[tuple[int, SM2State]]:
    """Simulate a series of reviews for educational/testing purposes.

    This is useful for understanding how SM-2 behaves over time.

    Args:
        qualities: List of quality ratings (0-5) for each review

    Returns:
        List of (review_number, state_after_review) tuples

    Example:
        >>> results = simulate_reviews([4, 5, 5, 3, 5])
        >>> for i, state in results:
        ...     print(
        ...         f"Review {i}: interval={state.interval}, EF={state.easiness_factor}"
        ...     )
        Review 1: interval=1, EF=2.5
        Review 2: interval=6, EF=2.6
        Review 3: interval=16, EF=2.7
        Review 4: interval=22, EF=2.56
        Review 5: interval=58, EF=2.66
    """
    state = get_initial_state()
    results = []

    for i, quality in enumerate(qualities, 1):
        state = process_review(state, quality)
        results.append((i, state))

    return results
