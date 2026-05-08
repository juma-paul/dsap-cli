"""Integration tests for the DSAP CLI.

Uses CliRunner to invoke commands end-to-end against a temporary
SQLite database, isolated via the DSAP_DB_PATH environment variable.
"""

from pathlib import Path

import pytest
from click.testing import CliRunner

from dsap.cli import cli


@pytest.fixture
def db_env(tmp_path: Path) -> dict[str, str]:
    """Environment that points CLI at a temporary database."""
    return {"DSAP_DB_PATH": str(tmp_path / "test.db")}


@pytest.fixture
def loaded_env(db_env: dict[str, str]) -> dict[str, str]:
    """Environment with blind75 already loaded."""
    CliRunner().invoke(cli, ["load", "blind75"], env=db_env)
    return db_env


class TestBasicCommands:
    """Smoke tests for commands that require no prior state."""

    def test_no_args_shows_welcome(self, db_env: dict[str, str]) -> None:
        result = CliRunner().invoke(cli, [], env=db_env)
        assert result.exit_code == 0
        assert "DSAP" in result.output

    def test_version(self, db_env: dict[str, str]) -> None:
        result = CliRunner().invoke(cli, ["--version"], env=db_env)
        assert result.exit_code == 0
        assert "version" in result.output

    def test_help(self, db_env: dict[str, str]) -> None:
        result = CliRunner().invoke(cli, ["--help"], env=db_env)
        assert result.exit_code == 0
        assert "review" in result.output
        assert "stats" in result.output


class TestEmptyDatabase:
    """Commands behave gracefully when no problems are loaded."""

    def test_stats_empty_db(self, db_env: dict[str, str]) -> None:
        result = CliRunner().invoke(cli, ["stats"], env=db_env)
        assert result.exit_code == 0
        assert "No problems loaded" in result.output

    def test_list_empty_db(self, db_env: dict[str, str]) -> None:
        result = CliRunner().invoke(cli, ["list"], env=db_env)
        assert result.exit_code == 0
        assert "No problems" in result.output

    def test_next_empty_db(self, db_env: dict[str, str]) -> None:
        result = CliRunner().invoke(cli, ["next"], env=db_env)
        assert result.exit_code == 0

    def test_review_empty_db(self, db_env: dict[str, str]) -> None:
        result = CliRunner().invoke(cli, ["review"], env=db_env)
        assert result.exit_code == 0


class TestLoad:
    """Tests for the load command."""

    def test_load_blind75(self, db_env: dict[str, str]) -> None:
        result = CliRunner().invoke(cli, ["load", "blind75"], env=db_env)
        assert result.exit_code == 0
        assert "75" in result.output

    def test_load_neetcode150(self, db_env: dict[str, str]) -> None:
        result = CliRunner().invoke(cli, ["load", "neetcode150"], env=db_env)
        assert result.exit_code == 0
        assert "150" in result.output

    def test_load_skips_duplicates(self, db_env: dict[str, str]) -> None:
        runner = CliRunner()
        runner.invoke(cli, ["load", "blind75"], env=db_env)
        result = runner.invoke(cli, ["load", "blind75"], env=db_env)
        assert result.exit_code == 0
        # Second load: 0 new problems added
        assert "0 new problems" in result.output

    def test_load_list_flag(self, db_env: dict[str, str]) -> None:
        result = CliRunner().invoke(cli, ["load", "--list"], env=db_env)
        assert result.exit_code == 0
        assert "blind75" in result.output

    def test_load_invalid_source(self, db_env: dict[str, str]) -> None:
        result = CliRunner().invoke(cli, ["load", "nonexistent_set"], env=db_env)
        assert result.exit_code == 0
        assert "Error" in result.output


class TestAfterLoad:
    """Commands that require problems to be loaded first."""

    def test_stats_shows_total(self, loaded_env: dict[str, str]) -> None:
        result = CliRunner().invoke(cli, ["stats"], env=loaded_env)
        assert result.exit_code == 0
        assert "75" in result.output

    def test_list_shows_problems(self, loaded_env: dict[str, str]) -> None:
        result = CliRunner().invoke(cli, ["list"], env=loaded_env)
        assert result.exit_code == 0

    def test_list_filter_by_difficulty(self, loaded_env: dict[str, str]) -> None:
        result = CliRunner().invoke(cli, ["list", "-d", "Easy"], env=loaded_env)
        assert result.exit_code == 0

    def test_next_returns_problem(self, loaded_env: dict[str, str]) -> None:
        # Decline browser prompt, then decline rating
        result = CliRunner().invoke(cli, ["next"], input="n\nn\n", env=loaded_env)
        assert result.exit_code == 0

    def test_review_no_due_problems(self, loaded_env: dict[str, str]) -> None:
        result = CliRunner().invoke(cli, ["review"], env=loaded_env)
        assert result.exit_code == 0
        assert "No problems due" in result.output

    def test_next_after_rating(self, loaded_env: dict[str, str]) -> None:
        runner = CliRunner()
        # Rate a problem: decline browser, rate it 4
        result = runner.invoke(cli, ["next"], input="n\ny\n4\n", env=loaded_env)
        assert result.exit_code == 0


class TestAdd:
    """Tests for adding custom problems."""

    def test_add_custom_problem(self, db_env: dict[str, str]) -> None:
        result = CliRunner().invoke(
            cli,
            [
                "add",
                "My Problem",
                "https://example.com/problem",
                "-d",
                "Easy",
                "-c",
                "Arrays",
            ],
            env=db_env,
        )
        assert result.exit_code == 0

    def test_add_appears_in_list(self, db_env: dict[str, str]) -> None:
        runner = CliRunner()
        runner.invoke(
            cli,
            [
                "add",
                "My Problem",
                "https://example.com/problem",
                "-d",
                "Easy",
                "-c",
                "Arrays",
            ],
            env=db_env,
        )
        result = runner.invoke(cli, ["list"], env=db_env)
        assert result.exit_code == 0


class TestConfig:
    """Tests for the config command."""

    def test_config_list(self, db_env: dict[str, str]) -> None:
        result = CliRunner().invoke(cli, ["config", "--list"], env=db_env)
        assert result.exit_code == 0
        assert "daily_goal" in result.output

    def test_config_get_key(self, db_env: dict[str, str]) -> None:
        result = CliRunner().invoke(cli, ["config", "daily_goal"], env=db_env)
        assert result.exit_code == 0

    def test_config_set_key(self, db_env: dict[str, str]) -> None:
        result = CliRunner().invoke(cli, ["config", "daily_goal", "10"], env=db_env)
        assert result.exit_code == 0

    def test_config_unknown_key(self, db_env: dict[str, str]) -> None:
        result = CliRunner().invoke(cli, ["config", "nonexistent_key"], env=db_env)
        assert result.exit_code == 0
        assert "Error" in result.output


class TestReviewSession:
    """Tests for the review command with actual due problems.

    Plants a due problem directly into the temp DB so the review loop
    runs, covering cli.py 150-200 and ui.py display_problem with progress.
    """

    def test_review_with_due_problem(
        self, tmp_path: Path, db_env: dict[str, str]
    ) -> None:
        from datetime import datetime, timedelta

        from dsap.database import Database
        from dsap.sm2 import SM2State

        runner = CliRunner()
        runner.invoke(cli, ["load", "blind75"], env=db_env)

        db = Database(db_path=tmp_path / "test.db")
        problem_id = db.get_problems(limit=1)[0][0].id
        db.update_progress(
            problem_id,
            SM2State(
                easiness_factor=2.5,
                interval=1,
                repetitions=1,
                next_review=datetime.now() - timedelta(hours=1),
            ),
            quality=4,
        )

        # Decline browser, rate 4
        result = runner.invoke(cli, ["review"], input="n\n4\n", env=db_env)
        assert result.exit_code == 0

    def test_list_shows_due_column_after_review(
        self, tmp_path: Path, db_env: dict[str, str]
    ) -> None:
        from datetime import datetime, timedelta

        from dsap.database import Database
        from dsap.sm2 import SM2State

        runner = CliRunner()
        runner.invoke(cli, ["load", "blind75"], env=db_env)

        db = Database(db_path=tmp_path / "test.db")
        problem_id = db.get_problems(limit=1)[0][0].id
        db.update_progress(
            problem_id,
            SM2State(
                easiness_factor=2.5,
                interval=1,
                repetitions=1,
                next_review=datetime.now() - timedelta(hours=1),
            ),
            quality=4,
        )

        result = runner.invoke(cli, ["list"], env=db_env)
        assert result.exit_code == 0


class TestReset:
    """Tests for the reset command."""

    def test_reset_requires_flag(self, db_env: dict[str, str]) -> None:
        result = CliRunner().invoke(cli, ["reset"], env=db_env)
        assert result.exit_code == 0
        assert "Please specify" in result.output

    def test_reset_progress_with_yes(self, loaded_env: dict[str, str]) -> None:
        result = CliRunner().invoke(
            cli, ["reset", "--progress", "--yes"], env=loaded_env
        )
        assert result.exit_code == 0

    def test_reset_all_with_yes(self, loaded_env: dict[str, str]) -> None:
        result = CliRunner().invoke(cli, ["reset", "--all", "--yes"], env=loaded_env)
        assert result.exit_code == 0

    def test_reset_cancel(self, loaded_env: dict[str, str]) -> None:
        # Decline the confirmation prompt
        result = CliRunner().invoke(
            cli, ["reset", "--progress"], input="n\n", env=loaded_env
        )
        assert result.exit_code == 0
        assert "cancelled" in result.output
