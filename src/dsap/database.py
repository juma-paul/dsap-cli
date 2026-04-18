"""SQLite Database Operations for DSAP.

This module handles all database operations including:
- Problem storage and retrieval
- Progress tracking with SM-2 state
- Session history for streak calculation
- Statistics aggregation
"""

import json
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path

from dsap.models import (
    Difficulty,
    Problem,
    ProblemProgress,
    Statistics,
)
from dsap.sm2 import SM2State


class Database:
    """SQLite database manager for DSAP.

    Handles all persistence operations including problems, progress,
    and session tracking.

    Usage:
        db = Database()
        db.add_problem(problem)
        due_problems = db.get_due_problems()
    """

    def __init__(self, db_path: Path | None = None):
        """Initialize the database.

        Args:
            db_path: Path to SQLite database file.
                    Defaults to ~/.dsap/dsap.db
        """
        if db_path is None:
            self.db_path = Path.home() / ".dsap" / "dsap.db"
        else:
            self.db_path = db_path

        # Ensure directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # Initialize schema
        self._initialize()

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        """Create a database connection with Row factory."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _initialize(self) -> None:
        """Create database tables if they don't exist."""
        with self._connect() as conn:
            conn.executescript("""
                -- Problems table: stores problem metadata
                CREATE TABLE IF NOT EXISTS problems (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    url TEXT NOT NULL UNIQUE,
                    difficulty TEXT NOT NULL CHECK(
                        difficulty IN ('Easy', 'Medium', 'Hard')
                    ),
                    category TEXT NOT NULL,
                    description TEXT DEFAULT '',
                    tags TEXT DEFAULT '[]',
                    problem_set TEXT DEFAULT 'custom',
                    problem_number INTEGER DEFAULT 0,
                    company_tags TEXT DEFAULT '[]',
                    hints TEXT DEFAULT '[]',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                -- Progress table: tracks SM-2 state and user progress
                CREATE TABLE IF NOT EXISTS progress (
                    problem_id INTEGER PRIMARY KEY,
                    easiness_factor REAL DEFAULT 2.5,
                    interval INTEGER DEFAULT 0,
                    repetitions INTEGER DEFAULT 0,
                    next_review TIMESTAMP,
                    last_reviewed TIMESTAMP,
                    attempts INTEGER DEFAULT 0,
                    solved INTEGER DEFAULT 0,
                    first_attempted TIMESTAMP,
                    solved_at TIMESTAMP,
                    last_quality INTEGER,
                    notes TEXT DEFAULT '',
                    time_spent_minutes INTEGER DEFAULT 0,
                    FOREIGN KEY (problem_id) REFERENCES problems(id) ON DELETE CASCADE
                );

                -- Sessions table: for streak tracking
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date DATE NOT NULL UNIQUE,
                    problems_reviewed INTEGER DEFAULT 0,
                    problems_due INTEGER DEFAULT 0,
                    average_quality REAL DEFAULT 0,
                    duration_minutes INTEGER DEFAULT 0,
                    notes TEXT DEFAULT '',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                -- Indexes for efficient queries
                CREATE INDEX IF NOT EXISTS idx_progress_next_review
                ON progress(next_review);

                CREATE INDEX IF NOT EXISTS idx_problems_difficulty
                ON problems(difficulty);

                CREATE INDEX IF NOT EXISTS idx_problems_category
                ON problems(category);

                CREATE INDEX IF NOT EXISTS idx_problems_set
                ON problems(problem_set);

                CREATE INDEX IF NOT EXISTS idx_sessions_date
                ON sessions(date);
            """)

    # ==================== Problem Operations ====================

    def add_problem(self, problem: Problem) -> int:
        """Add a problem to the database.

        Args:
            problem: Problem to add

        Returns:
            The ID of the newly added problem

        Raises:
            sqlite3.IntegrityError: If problem URL already exists
        """
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO problems
                (title, url, difficulty, category, description, tags,
                 problem_set, problem_number, company_tags, hints)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    problem.title,
                    str(problem.url),
                    problem.difficulty.value,
                    problem.category,
                    problem.description,
                    json.dumps(problem.tags),
                    problem.problem_set,
                    problem.problem_number,
                    json.dumps(problem.company_tags),
                    json.dumps(problem.hints),
                ),
            )
            return cursor.lastrowid or 0

    def add_problems(self, problems: list[Problem]) -> int:
        """Add multiple problems, skipping duplicates.

        Returns:
            Count of newly added problems
        """
        added = 0
        for problem in problems:
            try:
                self.add_problem(problem)
                added += 1
            except sqlite3.IntegrityError:
                # Duplicate URL, skip
                pass
        return added

    def get_problem(self, problem_id: int) -> Problem | None:
        """Get a problem by ID."""
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM problems WHERE id = ?", (problem_id,)
            ).fetchone()

            if row:
                return self._row_to_problem(row)
            return None

    def get_problems(
        self,
        difficulty: str | None = None,
        category: str | None = None,
        problem_set: str | None = None,
        due_only: bool = False,
        limit: int = 200,
    ) -> list[tuple[Problem, ProblemProgress | None]]:
        """Get problems with optional filters.

        Args:
            difficulty: Filter by difficulty (Easy/Medium/Hard)
            category: Filter by category
            problem_set: Filter by problem set name
            due_only: Only return problems due for review
            limit: Maximum number of problems to return

        Returns:
            List of (Problem, ProblemProgress or None) tuples
        """
        conditions = []
        params: list = []

        if difficulty:
            conditions.append("p.difficulty = ?")
            params.append(difficulty)

        if category:
            conditions.append("p.category = ?")
            params.append(category)

        if problem_set:
            conditions.append("p.problem_set = ?")
            params.append(problem_set)

        if due_only:
            now = datetime.now().isoformat()
            conditions.append("(pr.next_review <= ? OR pr.next_review IS NULL)")
            params.append(now)

        where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
        params.append(limit)

        query = f"""
            SELECT p.*, pr.*
            FROM problems p
            LEFT JOIN progress pr ON p.id = pr.problem_id
            {where_clause}
            ORDER BY p.problem_number ASC, p.id ASC
            LIMIT ?
        """

        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
            return [self._row_to_problem_with_progress(row) for row in rows]

    def delete_problem(self, problem_id: int) -> bool:
        """Delete a problem by ID."""
        with self._connect() as conn:
            cursor = conn.execute("DELETE FROM problems WHERE id = ?", (problem_id,))
            return cursor.rowcount > 0

    def delete_all_problems(self, problem_set: str | None = None) -> int:
        """Delete all problems, optionally filtered by set.

        Args:
            problem_set: If provided, only delete problems from this set

        Returns:
            Number of problems deleted
        """
        with self._connect() as conn:
            if problem_set:
                cursor = conn.execute(
                    "DELETE FROM problems WHERE problem_set = ?", (problem_set,)
                )
            else:
                cursor = conn.execute("DELETE FROM problems")
            return cursor.rowcount

    def reset_progress(self, problem_set: str | None = None) -> int:
        """Reset progress for all problems, optionally filtered by set.

        Args:
            problem_set: If provided, only reset progress for this set

        Returns:
            Number of progress records reset
        """
        with self._connect() as conn:
            if problem_set:
                cursor = conn.execute(
                    """
                    DELETE FROM progress
                    WHERE problem_id IN (
                        SELECT id FROM problems WHERE problem_set = ?
                    )
                """,
                    (problem_set,),
                )
            else:
                cursor = conn.execute("DELETE FROM progress")
            return cursor.rowcount

    # ==================== Progress Operations ====================

    def get_due_problems(
        self,
        limit: int = 10,
        difficulty: str | None = None,
        category: str | None = None,
        problem_set: str | None = None,
    ) -> list[tuple[Problem, ProblemProgress]]:
        """Get problems that are due for review.

        Problems are due if:
        - next_review is NULL (never reviewed), OR
        - next_review <= now

        Ordered by: next_review ASC (most overdue first)
        """
        now = datetime.now().isoformat()
        conditions = ["(pr.next_review <= ? OR pr.next_review IS NULL)"]
        params: list = [now]

        if difficulty:
            conditions.append("p.difficulty = ?")
            params.append(difficulty)

        if category:
            conditions.append("p.category = ?")
            params.append(category)

        if problem_set:
            conditions.append("p.problem_set = ?")
            params.append(problem_set)

        where_clause = " AND ".join(conditions)
        params.append(limit)

        query = f"""
            SELECT p.*, pr.*
            FROM problems p
            JOIN progress pr ON p.id = pr.problem_id
            WHERE {where_clause}
            ORDER BY pr.next_review ASC NULLS FIRST
            LIMIT ?
        """

        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
            return [
                (self._row_to_problem(row), self._row_to_progress(row)) for row in rows
            ]

    def get_new_problems(
        self,
        limit: int = 10,
        problem_set: str | None = None,
    ) -> list[Problem]:
        """Get problems that have never been reviewed."""
        conditions = ["pr.problem_id IS NULL"]
        params: list = []

        if problem_set:
            conditions.append("p.problem_set = ?")
            params.append(problem_set)

        where_clause = " AND ".join(conditions)
        params.append(limit)

        query = f"""
            SELECT p.*
            FROM problems p
            LEFT JOIN progress pr ON p.id = pr.problem_id
            WHERE {where_clause}
            ORDER BY p.problem_number ASC
            LIMIT ?
        """

        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
            return [self._row_to_problem(row) for row in rows]

    def get_next_recommendation(
        self,
        difficulty: str | None = None,
        category: str | None = None,
        problem_set: str | None = None,
        new_only: bool = False,
    ) -> tuple[Problem, ProblemProgress | None] | None:
        """Get the next recommended problem using SM-2 priorities.

        Priority order:
        1. Due problems (most overdue first)
        2. New problems (never reviewed)
        3. Hardest problems (lowest EF)
        """
        with self._connect() as conn:
            # Build common WHERE conditions
            conditions = []
            params: list = []

            if difficulty:
                conditions.append("p.difficulty = ?")
                params.append(difficulty)
            if category:
                conditions.append("p.category = ?")
                params.append(category)
            if problem_set:
                conditions.append("p.problem_set = ?")
                params.append(problem_set)

            base_where = " AND ".join(conditions) if conditions else "1=1"

            # Priority 1: Due problems
            if not new_only:
                now = datetime.now().isoformat()
                due_query = f"""
                    SELECT p.*, pr.*
                    FROM problems p
                    JOIN progress pr ON p.id = pr.problem_id
                    WHERE {base_where}
                    AND (pr.next_review <= ? OR pr.next_review IS NULL)
                    ORDER BY pr.next_review ASC NULLS FIRST
                    LIMIT 1
                """
                row = conn.execute(due_query, params + [now]).fetchone()
                if row:
                    return self._row_to_problem_with_progress(row)

            # Priority 2: New problems
            new_query = f"""
                SELECT p.*, NULL as problem_id, NULL as easiness_factor,
                       NULL as interval, NULL as repetitions, NULL as next_review,
                       NULL as last_reviewed, NULL as attempts, NULL as solved,
                       NULL as first_attempted, NULL as solved_at,
                       NULL as last_quality, NULL as notes,
                       NULL as time_spent_minutes
                FROM problems p
                LEFT JOIN progress pr ON p.id = pr.problem_id
                WHERE {base_where}
                AND pr.problem_id IS NULL
                ORDER BY p.problem_number ASC
                LIMIT 1
            """
            row = conn.execute(new_query, params).fetchone()
            if row:
                return (self._row_to_problem(row), None)

            # Priority 3: Hardest problems (lowest EF)
            if not new_only:
                hard_query = f"""
                    SELECT p.*, pr.*
                    FROM problems p
                    JOIN progress pr ON p.id = pr.problem_id
                    WHERE {base_where}
                    ORDER BY pr.easiness_factor ASC
                    LIMIT 1
                """
                row = conn.execute(hard_query, params).fetchone()
                if row:
                    return self._row_to_problem_with_progress(row)

            return None

    def update_progress(
        self,
        problem_id: int,
        sm2_state: SM2State,
        quality: int,
    ) -> None:
        """Update progress after a review.

        Creates the progress record if it doesn't exist.
        """
        now = datetime.now()

        with self._connect() as conn:
            # Check if progress exists
            existing = conn.execute(
                "SELECT 1 FROM progress WHERE problem_id = ?", (problem_id,)
            ).fetchone()

            if existing:
                # Update existing
                conn.execute(
                    """
                    UPDATE progress SET
                        easiness_factor = ?,
                        interval = ?,
                        repetitions = ?,
                        next_review = ?,
                        last_reviewed = ?,
                        attempts = attempts + 1,
                        solved_at = CASE
                            WHEN ? >= 3 AND solved = 0 THEN ?
                            ELSE solved_at
                        END,
                        solved_at = CASE 
                            WHEN ? >= 3 AND solved = 0 THEN ? 
                            ELSE solved_at 
                        END,
                        last_quality = ?
                    WHERE problem_id = ?
                """,
                    (
                        sm2_state.easiness_factor,
                        sm2_state.interval,
                        sm2_state.repetitions,
                        sm2_state.next_review.isoformat()
                        if sm2_state.next_review
                        else None,
                        sm2_state.last_reviewed.isoformat()
                        if sm2_state.last_reviewed
                        else None,
                        quality,
                        quality,
                        now.isoformat(),
                        quality,
                        problem_id,
                    ),
                )
            else:
                # Create new
                conn.execute(
                    """
                    INSERT INTO progress (
                        problem_id, easiness_factor, interval, repetitions,
                        next_review, last_reviewed, attempts, solved,
                        first_attempted, solved_at, last_quality
                    ) VALUES (?, ?, ?, ?, ?, ?, 1, ?, ?, ?, ?)
                """,
                    (
                        problem_id,
                        sm2_state.easiness_factor,
                        sm2_state.interval,
                        sm2_state.repetitions,
                        sm2_state.next_review.isoformat()
                        if sm2_state.next_review
                        else None,
                        sm2_state.last_reviewed.isoformat()
                        if sm2_state.last_reviewed
                        else None,
                        1 if quality >= 3 else 0,
                        now.isoformat(),
                        now.isoformat() if quality >= 3 else None,
                        quality,
                    ),
                )

            # Update session for streak tracking
            self._update_daily_session(conn)

    def ensure_progress_exists(self, problem_id: int) -> None:
        """Ensure a progress record exists for a problem."""
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO progress (problem_id)
                VALUES (?)
            """,
                (problem_id,),
            )

    # ==================== Statistics ====================

    def get_statistics(self) -> Statistics:
        """Get comprehensive statistics."""
        with self._connect() as conn:
            # Total problems
            total = conn.execute("SELECT COUNT(*) FROM problems").fetchone()[0]

            # Progress stats
            progress_stats = conn.execute("""
                SELECT
                    COUNT(*) as reviewed,
                    SUM(CASE WHEN solved = 1 THEN 1 ELSE 0 END) as solved,
                    AVG(easiness_factor) as avg_ef,
                    SUM(attempts) as total_reviews
                FROM progress
            """).fetchone()

            # Due counts
            now = datetime.now().isoformat()
            week_later = (datetime.now() + timedelta(days=7)).isoformat()

            due_today = conn.execute(
                """
                SELECT COUNT(*) FROM progress
                WHERE next_review <= ? OR next_review IS NULL
            """,
                (now,),
            ).fetchone()[0]

            due_week = conn.execute(
                """
                SELECT COUNT(*) FROM progress
                WHERE next_review <= ?
            """,
                (week_later,),
            ).fetchone()[0]

            # Difficulty breakdown
            diff_stats = conn.execute("""
                SELECT
                    p.difficulty,
                    COUNT(*) as total,
                    SUM(CASE WHEN pr.solved = 1 THEN 1 ELSE 0 END) as solved
                FROM problems p
                LEFT JOIN progress pr ON p.id = pr.problem_id
                GROUP BY p.difficulty
            """).fetchall()

            diff_data = {row["difficulty"]: dict(row) for row in diff_stats}

            # Streaks
            current_streak = self._calculate_current_streak(conn)
            best_streak = self._calculate_best_streak(conn)

            return Statistics(
                total_problems=total,
                reviewed_problems=progress_stats["reviewed"] or 0,
                solved_problems=progress_stats["solved"] or 0,
                due_today=due_today,
                due_this_week=due_week,
                average_easiness_factor=round(progress_stats["avg_ef"] or 2.5, 2),
                current_streak=current_streak,
                best_streak=best_streak,
                total_reviews=progress_stats["total_reviews"] or 0,
                easy_total=diff_data.get("Easy", {}).get("total", 0),
                easy_solved=diff_data.get("Easy", {}).get("solved", 0) or 0,
                medium_total=diff_data.get("Medium", {}).get("total", 0),
                medium_solved=diff_data.get("Medium", {}).get("solved", 0) or 0,
                hard_total=diff_data.get("Hard", {}).get("total", 0),
                hard_solved=diff_data.get("Hard", {}).get("solved", 0) or 0,
            )

    def get_categories(self) -> list[str]:
        """Get all unique categories."""
        with self._connect() as conn:
            rows = conn.execute("""
                SELECT DISTINCT category FROM problems ORDER BY category
            """).fetchall()
            return [row["category"] for row in rows]

    def get_problem_sets(self) -> list[str]:
        """Get all unique problem set names."""
        with self._connect() as conn:
            rows = conn.execute("""
                SELECT DISTINCT problem_set FROM problems ORDER BY problem_set
            """).fetchall()
            return [row["problem_set"] for row in rows]

    # ==================== Session & Streak Tracking ====================

    def _update_daily_session(self, conn: sqlite3.Connection) -> None:
        """Update or create today's session record."""
        today = datetime.now().date().isoformat()

        conn.execute(
            """
            INSERT INTO sessions (date, problems_reviewed)
            VALUES (?, 1)
            ON CONFLICT(date) DO UPDATE SET
                problems_reviewed = problems_reviewed + 1
        """,
            (today,),
        )

    def _calculate_current_streak(self, conn: sqlite3.Connection) -> int:
        """Calculate the current daily streak.

        A streak is consecutive days with at least one review.
        Today counts toward the streak even if not yet reviewed.
        """
        today = datetime.now().date()
        streak = 0

        for days_ago in range(365):  # Max 1 year lookback
            check_date = (today - timedelta(days=days_ago)).isoformat()

            reviewed = conn.execute(
                """
                SELECT COUNT(*) FROM sessions
                WHERE date = ? AND problems_reviewed > 0
            """,
                (check_date,),
            ).fetchone()[0]

            if reviewed > 0:
                streak += 1
            elif days_ago > 0:
                # Allow missing today, but break on any past gap
                break

        return streak

    def _calculate_best_streak(self, conn: sqlite3.Connection) -> int:
        """Calculate the longest streak ever."""
        rows = conn.execute("""
            SELECT date FROM sessions
            WHERE problems_reviewed > 0
            ORDER BY date ASC
        """).fetchall()

        if not rows:
            return 0

        dates = [datetime.fromisoformat(row["date"]).date() for row in rows]
        best_streak = 1
        current_streak = 1

        for i in range(1, len(dates)):
            if (dates[i] - dates[i - 1]).days == 1:
                current_streak += 1
                best_streak = max(best_streak, current_streak)
            else:
                current_streak = 1

        return best_streak

    # ==================== Helper Methods ====================

    def _row_to_problem(self, row: sqlite3.Row) -> Problem:
        """Convert a database row to a Problem model."""
        return Problem(
            id=row["id"],
            title=row["title"],
            url=row["url"],
            difficulty=Difficulty(row["difficulty"]),
            category=row["category"],
            description=row["description"] or "",
            tags=json.loads(row["tags"] or "[]"),
            problem_set=row["problem_set"],
            problem_number=row["problem_number"],
            company_tags=json.loads(row["company_tags"] or "[]"),
            hints=json.loads(row["hints"] or "[]"),
            created_at=datetime.fromisoformat(row["created_at"])
            if row["created_at"]
            else None,
        )

    def _row_to_progress(self, row: sqlite3.Row) -> ProblemProgress:
        """Convert a database row to a ProblemProgress model."""
        return ProblemProgress(
            problem_id=row["problem_id"],
            easiness_factor=row["easiness_factor"] or 2.5,
            interval=row["interval"] or 0,
            repetitions=row["repetitions"] or 0,
            next_review=datetime.fromisoformat(row["next_review"])
            if row["next_review"]
            else None,
            last_reviewed=datetime.fromisoformat(row["last_reviewed"])
            if row["last_reviewed"]
            else None,
            attempts=row["attempts"] or 0,
            solved=bool(row["solved"]),
            first_attempted=datetime.fromisoformat(row["first_attempted"])
            if row["first_attempted"]
            else None,
            solved_at=datetime.fromisoformat(row["solved_at"])
            if row["solved_at"]
            else None,
            last_quality=row["last_quality"],
            notes=row["notes"] or "",
            time_spent_minutes=row["time_spent_minutes"] or 0,
        )

    def _row_to_problem_with_progress(
        self, row: sqlite3.Row
    ) -> tuple[Problem, ProblemProgress | None]:
        """Convert a joined row to Problem and optional ProblemProgress."""
        problem = self._row_to_problem(row)

        if row["problem_id"] is not None:
            progress = self._row_to_progress(row)
            return (problem, progress)

        return (problem, None)
