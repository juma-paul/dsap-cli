"""DSAP CLI - DSA Practice with Spaced Repetition.

Main command-line interface using Click.

Commands:
  dsap review  - Start a review session with due problems
  dsap next    - Get next recommended problem
  dsap list    - List problems with filters
  dsap stats   - Show statistics and progress
  dsap load    - Load a curated problem set
  dsap add     - Add a custom problem
  dsap config  - Manage configuration
  dsap reset   - Reset problems and/or progress
"""

import click
import yaml

from dsap import __version__
from dsap.config import get_config
from dsap.database import Database
from dsap.models import Difficulty, Problem
from dsap.problem_sets import list_bundled_sets, load_problem_set
from dsap.sm2 import SM2State, process_review
from dsap.ui import (
    console,
    display_error,
    display_info,
    display_problem,
    display_problem_list,
    display_review_feedback,
    display_session_summary,
    display_stats,
    display_success,
    display_warning,
    display_welcome,
    prompt_open_browser,
    prompt_quality_rating,
)


def normalize_set_name(name: str | None) -> str | None:
    """Normalize problem set names to their canonical form."""
    if name is None:
        return None

    name_lower = name.lower().replace(" ", "").replace("_", "")

    mapping = {
        "blind75": "Blind 75",
        "neetcode150": "NeetCode 150",
        "grind75": "Grind 75",
    }

    return mapping.get(name_lower, name)


@click.group(invoke_without_command=True)
@click.version_option(version=__version__, prog_name="dsap")
@click.pass_context
def cli(ctx: click.Context) -> None:
    r"""DSAP - DSA Practice with Spaced Repetition.

    Master data structures and algorithms with scientifically-proven
    spaced repetition (SM-2 algorithm).

    \b
    Quick Start:
      dsap load blind75    Load the Blind 75 problems
      dsap review          Start practicing
      dsap stats           Check your progress

    \b
    Examples:
      dsap review --limit 5        Review up to 5 problems
      dsap next --difficulty Easy  Get an easy problem
      dsap list --due              Show problems due today
    """
    if ctx.invoked_subcommand is None:
        display_welcome()


@cli.command()
@click.option(
    "--limit", "-n", default=10, help="Maximum problems to review (default: 10)"
)
@click.option(
    "--difficulty",
    "-d",
    type=click.Choice(["Easy", "Medium", "Hard"], case_sensitive=False),
    help="Filter by difficulty",
)
@click.option("--category", "-c", help="Filter by category")
@click.option(
    "--set",
    "-s",
    "problem_set",
    help="Filter by problem set (e.g., blind75, neetcode150)",
)
def review(limit: int, difficulty: str, category: str, problem_set: str) -> None:
    r"""Start a review session with due problems.

    Reviews problems that are due based on SM-2 scheduling.
    After solving each problem, rate your recall quality (0-5).

    \b
    Example:
      dsap review              Review up to 10 due problems
      dsap review -n 5         Review up to 5 problems
      dsap review -d Medium    Review only medium difficulty
      dsap review -s blind75   Review only Blind 75 problems
    """
    db = Database()
    config = get_config()

    # Use config's preferred_set if not specified
    if not problem_set:
        problem_set = config.get("preferred_set")

    # Normalize the set name
    normalized = normalize_set_name(problem_set)
    if normalized is None:
        raise ValueError("Invalid problem set name")
    problem_set = normalized

    # Get due problems
    due_problems = db.get_due_problems(
        limit=limit,
        difficulty=difficulty,
        category=category,
        problem_set=problem_set,
    )

    if not due_problems:
        # Check if there are new problems to start
        new_problems = db.get_new_problems(limit=limit, problem_set=problem_set)
        if new_problems:
            console.print(
                f"[green]No problems due![/green] "
                f"You have {len(new_problems)} new problems to start."
            )
            console.print("Run [bold]dsap next[/bold] to get a new problem.")
        else:
            console.print(
                "[green]No problems due for review![/green] "
                "Great job keeping up with your practice."
            )
        return

    console.print(
        f"[bold]Starting review session: {len(due_problems)} problems due[/bold]"
    )
    console.print()

    qualities: list[int] = []
    reviewed = 0

    for i, (problem, progress) in enumerate(due_problems, 1):
        # Display problem
        display_problem(
            problem,
            progress=progress,
            index=i,
            total=len(due_problems),
        )

        # Prompt to open browser
        auto_open = config.get("auto_open_browser")
        prompt_open_browser(str(problem.url), auto_open=auto_open)

        # Get quality rating
        quality = prompt_quality_rating()

        if quality is None:
            # User wants to quit
            console.print()
            display_warning("Session paused. Progress saved.")
            break

        # Update SM-2 state
        current_state = SM2State(
            easiness_factor=progress.easiness_factor,
            interval=progress.interval,
            repetitions=progress.repetitions,
        )
        new_state = process_review(current_state, quality)

        # Save to database
        if problem.id is None:
            raise ValueError("Problem has no ID")
        db.update_progress(problem.id, new_state, quality)

        # Show feedback
        display_review_feedback(quality, new_state.interval)

        qualities.append(quality)
        reviewed += 1

    # Show session summary
    display_session_summary(reviewed, len(due_problems), qualities)


@cli.command()
@click.option(
    "--difficulty",
    "-d",
    type=click.Choice(["Easy", "Medium", "Hard"], case_sensitive=False),
    help="Filter by difficulty",
)
@click.option("--category", "-c", help="Filter by category")
@click.option(
    "--set",
    "-s",
    "problem_set",
    help="Filter by problem set (e.g., blind75, neetcode150)",
)
@click.option(
    "--new-only", "-n", is_flag=True, help="Only show problems never attempted"
)
def next(difficulty: str, category: str, problem_set: str, new_only: bool) -> None:
    r"""Get the next recommended problem to practice.

    Recommends based on:
    1. Problems due for review (highest priority)
    2. New problems you haven't tried yet
    3. Problems with low easiness factors (harder for you)

    \b
    Example:
      dsap next                  Get next recommended problem
      dsap next -d Easy          Get an easy problem
      dsap next --new-only       Get a new problem only
      dsap next -s blind75       Get from Blind 75 only
    """
    db = Database()
    config = get_config()

    # Use config's preferred_set if not specified
    if not problem_set:
        problem_set = config.get("preferred_set")

    # Normalize the set name
    normalized = normalize_set_name(problem_set)
    if normalized is None:
        raise ValueError("Invalid problem set name")
    problem_set = normalized

    result = db.get_next_recommendation(
        difficulty=difficulty,
        category=category,
        problem_set=problem_set,
        new_only=new_only,
    )

    if not result:
        if difficulty or category:
            display_warning("No problems found matching your filters.")
        else:
            display_info("No problems available. Try loading a problem set:")
            console.print("  dsap load blind75")
        return

    problem, progress = result

    # Ensure progress record exists
    if progress is None:
        if problem.id is None:
            raise ValueError("Problem has no ID")

        db.ensure_progress_exists(problem.id)

    # Display the problem
    display_problem(
        problem,
        progress=progress,
        show_hints=config.get("show_hints"),
    )

    # Prompt to open and optionally rate
    auto_open = config.get("auto_open_browser")
    opened = prompt_open_browser(str(problem.url), auto_open=auto_open)

    if opened:
        console.print()
        rate_now = click.confirm("Rate this problem now?", default=True)

        if rate_now:
            quality = prompt_quality_rating()

            if quality is not None:
                current_state = SM2State(
                    easiness_factor=progress.easiness_factor if progress else 2.5,
                    interval=progress.interval if progress else 0,
                    repetitions=progress.repetitions if progress else 0,
                )
                new_state = process_review(current_state, quality)

                if problem.id is None:
                    raise ValueError("Problem has no ID")
                db.update_progress(problem.id, new_state, quality)

                display_review_feedback(quality, new_state.interval)


@cli.command("list")
@click.option(
    "--difficulty",
    "-d",
    type=click.Choice(["Easy", "Medium", "Hard"], case_sensitive=False),
    help="Filter by difficulty",
)
@click.option("--category", "-c", help="Filter by category")
@click.option("--set", "problem_set", help="Filter by problem set (e.g., blind75)")
@click.option("--due", is_flag=True, help="Show only problems due for review")
@click.option(
    "--limit", "-n", default=200, help="Maximum problems to show (default: 200)"
)
def list_problems(
    difficulty: str,
    category: str,
    problem_set: str,
    due: bool,
    limit: int,
) -> None:
    r"""List all problems with optional filters.

    \b
    Example:
      dsap list                    List all problems
      dsap list --due              Show only due problems
      dsap list -d Hard            Show only hard problems
      dsap list --set blind75      Show Blind 75 problems
    """
    db = Database()

    # Normalize set name
    normalized = normalize_set_name(problem_set)
    if normalized is None:
        raise ValueError("Invalid problem set name")
    problem_set = normalized

    problems = db.get_problems(
        difficulty=difficulty,
        category=category,
        problem_set=problem_set,
        due_only=due,
        limit=limit,
    )

    if not problems:
        if difficulty or category or problem_set or due:
            display_warning("No problems found matching your filters.")
        else:
            display_info("No problems loaded. Try:")
            console.print("  dsap load blind75")
        return

    display_problem_list(problems)


@cli.command()
def stats() -> None:
    """Show your practice statistics and progress.

    Displays:
    - Total and solved problems
    - Problems due today and this week
    - Current and best streaks
    - Difficulty breakdown with progress bars
    """
    db = Database()
    statistics = db.get_statistics()

    if statistics.total_problems == 0:
        display_info("No problems loaded yet. Try:")
        console.print("  dsap load blind75")
        return

    display_stats(statistics)


@cli.command()
@click.argument("source", required=False)
@click.option("--list", "show_list", is_flag=True, help="List available problem sets")
def load(source: str, show_list: bool) -> None:
    r"""Load a curated problem set.

    \b
    Available sets:
      blind75      - Blind 75 essential problems
      neetcode150  - NeetCode 150 extended set
      grind75      - Grind 75 flexible plan

    \b
    Example:
      dsap load blind75           Load Blind 75
      dsap load --list            Show available sets
      dsap load ./custom.yaml     Load custom YAML file
    """
    if show_list:
        console.print("[bold]Available Problem Sets:[/bold]")
        console.print()
        for name, description in list_bundled_sets().items():
            console.print(f"  [cyan]{name}[/cyan] - {description}")
        console.print()
        console.print("Usage: dsap load <set_name>")
        return

    if not source:
        display_error("Please specify a problem set or use --list")
        return

    try:
        with console.status(f"Loading {source}..."):
            problems = load_problem_set(source)

        db = Database()
        added = db.add_problems(problems)

        display_success(
            f"Loaded {added} new problems from '{source}' "
            f"({len(problems)} total in set)"
        )

        if added < len(problems):
            display_info(
                f"{len(problems) - added} problems were already in your database"
            )

    except FileNotFoundError as e:
        display_error(str(e))
    except ValueError as e:
        display_error(str(e))
    except yaml.YAMLError as e:
        display_error(f"Failed to parse YAML file: {e}")
    except OSError as e:
        display_error(f"Failed to read file: {e}")


@cli.command()
@click.argument("title")
@click.argument("url")
@click.option(
    "--difficulty",
    "-d",
    required=True,
    type=click.Choice(["Easy", "Medium", "Hard"], case_sensitive=False),
    help="Problem difficulty",
)
@click.option(
    "--category",
    "-c",
    required=True,
    help="Problem category (e.g., 'Arrays', 'Dynamic Programming')",
)
@click.option("--description", help="Brief problem description")
@click.option("--tags", help="Comma-separated tags")
def add(
    title: str,
    url: str,
    difficulty: str,
    category: str,
    description: str,
    tags: str,
) -> None:
    r"""Add a custom problem.

    \b
    Example:
      dsap add "Two Sum" "https://leetcode.com/problems/two-sum" \\
          -d Easy -c "Arrays & Hashing"
    """
    tag_list = [t.strip() for t in tags.split(",")] if tags else []

    try:
        problem = Problem(
            title=title,
            url=url,
            difficulty=Difficulty.from_string(difficulty),
            category=category,
            description=description or "",
            tags=tag_list,
            problem_set="custom",
        )

        db = Database()
        problem_id = db.add_problem(problem)

        display_success(f"Added '{title}' with ID {problem_id}")

    except (ValueError, TypeError) as e:
        display_error(f"Failed to add problem: {e}")


@cli.command()
@click.argument("key", required=False)
@click.argument("value", required=False)
@click.option(
    "--list", "show_list", is_flag=True, help="Show all configuration options"
)
@click.option("--reset", is_flag=True, help="Reset configuration to defaults")
def config(key: str, value: str, show_list: bool, reset: bool) -> None:
    r"""View or set configuration options.

    \b
    Options:
      daily_goal           Number of problems per day (default: 5)
      preferred_difficulty Preferred difficulty (Easy/Medium/Hard/None)
      preferred_set        Default problem set (blind75/neetcode150/grind75/None)
      show_hints           Show hints for problems (true/false)
      auto_open_browser    Auto-open problems in browser (true/false)

    \b
    Example:
      dsap config --list                  Show all settings
      dsap config daily_goal              View daily goal
      dsap config daily_goal 10           Set daily goal to 10
      dsap config preferred_set blind75   Focus on Blind 75
      dsap config --reset                 Reset to defaults
    """
    cfg = get_config()

    if reset:
        cfg.reset()
        display_success("Configuration reset to defaults")
        return

    if show_list:
        console.print("[bold]Configuration:[/bold]")
        console.print()
        for k, v in cfg.all().items():
            console.print(f"  {k}: [cyan]{v}[/cyan]")
        return

    if key and value:
        try:
            cfg.set(key, value)
            display_success(f"Set {key} = {value}")
        except ValueError as e:
            display_error(str(e))
    elif key:
        val = cfg.get(key)
        if val is not None:
            console.print(f"{key}: [cyan]{val}[/cyan]")
        else:
            display_error(f"Unknown configuration key: {key}")
    else:
        # Show help
        console.print("Usage: dsap config [key] [value]")
        console.print("       dsap config --list")


@cli.command()
@click.option(
    "--problems",
    "-p",
    is_flag=True,
    help="Delete all problems (keeps progress history)",
)
@click.option(
    "--progress", "-r", is_flag=True, help="Reset progress only (keeps problems)"
)
@click.option(
    "--set", "-s", "problem_set", help="Only reset specific problem set (e.g., blind75)"
)
@click.option(
    "--all",
    "-a",
    "reset_all",
    is_flag=True,
    help="Reset everything (problems and progress)",
)
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation prompt")
def reset(
    problems: bool,
    progress: bool,
    problem_set: str,
    reset_all: bool,
    yes: bool,
) -> None:
    r"""Reset problems and/or progress.

    \b
    Example:
      dsap reset --all              Reset everything
      dsap reset --problems         Delete all problems
      dsap reset --progress         Reset progress only
      dsap reset -s blind75 --all   Reset only Blind 75
    """
    if not (problems or progress or reset_all):
        display_error("Please specify what to reset: --problems, --progress, or --all")
        console.print("\nRun [bold]dsap reset --help[/bold] for options.")
        return

    db = Database()

    # Normalize set name
    normalized = normalize_set_name(problem_set)
    if normalized is None:
        raise ValueError("Invalid problem set name")
    problem_set = normalized

    # Build description of what will be reset
    scope = f"'{problem_set}'" if problem_set else "all"
    actions = []
    if reset_all or problems:
        actions.append("delete problems")
    if reset_all or progress:
        actions.append("reset progress")

    action_str = " and ".join(actions)

    # Confirm
    if not yes:
        confirmed = click.confirm(
            f"This will {action_str} for {scope} problems. Continue?",
            default=False,
        )
        if not confirmed:
            display_info("Reset cancelled.")
            return

    # Perform reset
    if reset_all or progress:
        count = db.reset_progress(problem_set)
        display_success(f"Reset progress for {count} problems")

    if reset_all or problems:
        count = db.delete_all_problems(problem_set)
        display_success(f"Deleted {count} problems")


def main() -> None:
    """Entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()
