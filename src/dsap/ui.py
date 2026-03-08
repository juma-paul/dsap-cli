"""Rich Terminal UI Components for DSAP.

Provides beautiful terminal output using Rich library:
- Problem display with clickable links (OSC 8 hyperlinks)
- Statistics tables and progress bars
- Interactive quality rating prompts
- Session status displays
"""

import webbrowser

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm
from rich.style import Style
from rich.table import Table

from dsap.models import Difficulty, Problem, ProblemProgress, Statistics


# Global console instance
console = Console()

# Difficulty color styles
DIFFICULTY_STYLES: dict[Difficulty, Style] = {
    Difficulty.EASY: Style(color="green", bold=True),
    Difficulty.MEDIUM: Style(color="yellow", bold=True),
    Difficulty.HARD: Style(color="red", bold=True),
}


def make_link(url: str, text: str) -> str:
    """Create a Rich markup hyperlink.

    Rich automatically handles OSC 8 hyperlinks in supported terminals
    (iTerm2, Windows Terminal, VSCode terminal, etc.)

    Args:
        url: The URL to link to
        text: The display text

    Returns:
        Rich markup string with link
    """
    return f"[link={url}]{text}[/link]"


def display_welcome() -> None:
    """Display welcome message when dsap is run without arguments."""
    welcome = """
[bold cyan]DSAP[/bold cyan] - DSA Practice with Spaced Repetition

[bold]Quick Start:[/bold]
  dsap load blind75    Load the Blind 75 problem set
  dsap review          Start reviewing due problems
  dsap stats           Check your progress

[bold]Commands:[/bold]
  dsap --help          See all available commands
  dsap <cmd> --help    Get help for a specific command

[dim]Master algorithms with scientifically-proven spaced repetition (SM-2)[/dim]
"""
    console.print(Panel(welcome.strip(), border_style="blue", box=box.ROUNDED))


def display_problem(
    problem: Problem,
    progress: ProblemProgress | None = None,
    index: int | None = None,
    total: int | None = None,
    show_hints: bool = False,
) -> None:
    """Display a problem in a beautiful panel with clickable link.

    Args:
        problem: The problem to display
        progress: Optional progress data
        index: Current problem index (for "Problem 1/5" display)
        total: Total problems in session
        show_hints: Whether to show hints
    """
    lines: list[str] = []

    # Title as clickable link
    title_link = make_link(str(problem.url), problem.title)
    lines.append(f"[bold cyan]{title_link}[/bold cyan]")
    lines.append("")

    # URL (also clickable, shown separately for clarity)
    lines.append(f"[dim]{make_link(str(problem.url), str(problem.url))}[/dim]")
    lines.append("")

    # Metadata row
    diff_style = DIFFICULTY_STYLES.get(problem.difficulty, Style())
    lines.append(
        f"[bold]Difficulty:[/bold] [{diff_style}]{problem.difficulty.value}[/]  "
        f"[bold]Category:[/bold] {problem.category}"
    )

    # Problem set info
    if problem.problem_set != "custom":
        lines.append(
            f"[bold]Set:[/bold] {problem.problem_set} #{problem.problem_number}"
        )

    # Tags
    if problem.tags:
        tags_str = " ".join(f"[dim]#{tag}[/dim]" for tag in problem.tags[:6])
        lines.append(f"[bold]Tags:[/bold] {tags_str}")

    # Company tags
    if problem.company_tags:
        companies = ", ".join(problem.company_tags[:5])
        if len(problem.company_tags) > 5:
            companies += f" +{len(problem.company_tags) - 5} more"
        lines.append(f"[bold]Companies:[/bold] {companies}")

    # Description
    if problem.description:
        lines.append("")
        lines.append(f"[italic]{problem.description}[/italic]")

    # Progress info
    if progress:
        lines.append("")
        lines.append("[bold]Your Progress:[/bold]")
        status = (
            "[green]Solved[/green]"
            if progress.solved
            else "[yellow]In Progress[/yellow]"
        )
        lines.append(f"  Status: {status} | Attempts: {progress.attempts}")
        lines.append(
            f"  EF: {progress.easiness_factor:.2f} | Interval: {progress.interval} days"
        )
        if progress.next_review:
            lines.append(f"  Next review: {progress.next_review.strftime('%Y-%m-%d')}")

    # Hints (optional)
    if show_hints and problem.hints:
        lines.append("")
        lines.append("[bold]Hints:[/bold]")
        for i, hint in enumerate(problem.hints, 1):
            lines.append(f"  {i}. [dim]{hint}[/dim]")

    # Build panel title
    if index is not None and total is not None:
        title = f"Problem {index}/{total}"
    else:
        title = "Problem"

    panel = Panel(
        "\n".join(lines),
        title=f"[bold white]{title}[/bold white]",
        border_style="blue",
        box=box.ROUNDED,
    )

    console.print(panel)


def prompt_open_browser(url: str, auto_open: bool = True) -> bool:
    """Prompt user to open problem in browser.

    Args:
        url: URL to open
        auto_open: If True, ask to open; if False, just inform

    Returns:
        True if browser was opened
    """
    console.print()

    if auto_open:
        open_it = Confirm.ask(
            "[bold]Open in browser?[/bold]",
            default=True,
        )
        if open_it:
            webbrowser.open(str(url))
            console.print(
                "[dim]Opened in browser. Solve the problem, then return here.[/dim]"
            )
            return True
    else:
        console.print("[dim]Click the link above to open the problem.[/dim]")

    return False


def prompt_quality_rating() -> int | None:
    """Prompt user for quality rating after reviewing a problem.

    Returns:
        Quality rating (0-5) or None if user wants to quit
    """
    console.print()
    console.print("[bold]How well did you recall this problem?[/bold]")
    console.print()

    # Display rating options with colors
    ratings = [
        ("5", "green", "Perfect - instant recall, no hesitation"),
        ("4", "green", "Good - correct, but had to think"),
        ("3", "yellow", "Hard - struggled but eventually solved"),
        ("2", "red", "Forgot - wrong, but solution was familiar"),
        ("1", "red", "Blackout - wrong, barely recognized solution"),
        ("0", "red", "Total blackout - no memory at all"),
    ]

    for num, color, desc in ratings:
        console.print(f"  [{color}]{num}[/{color}] - {desc}")

    console.print("  [dim]q[/dim] - Quit session")
    console.print()

    while True:
        try:
            response = console.input("[bold]Rating (0-5 or q): [/bold]").strip().lower()

            if response == "q":
                return None

            quality = int(response)
            if 0 <= quality <= 5:
                return quality

            console.print("[red]Please enter a number between 0 and 5[/red]")
        except ValueError:
            console.print("[red]Invalid input. Enter 0-5 or 'q'[/red]")


def display_review_feedback(quality: int, next_interval: int) -> None:
    """Display feedback after a review.

    Args:
        quality: The quality rating given
        next_interval: Days until next review
    """
    console.print()

    if quality >= 4:
        emoji = "[green]"
        message = "Excellent!"
    elif quality == 3:
        emoji = "[yellow]"
        message = "Good effort!"
    else:
        emoji = "[red]"
        message = "Keep practicing!"

    interval_text = "tomorrow" if next_interval == 1 else f"in {next_interval} days"

    console.print(f"{emoji}{message}[/] Next review: {interval_text}")
    console.print()


def display_stats(stats: Statistics) -> None:
    """Display comprehensive statistics in a beautiful format."""
    # Main stats panel
    main_lines = [
        f"[bold]Total Problems:[/bold] {stats.total_problems}",
        f"[bold]Solved:[/bold] [green]{stats.solved_problems}[/green] ({stats.solved_percentage}%)",
        f"[bold]Reviewed:[/bold] {stats.reviewed_problems}",
        "",
        f"[bold]Due Today:[/bold] [yellow]{stats.due_today}[/yellow]",
        f"[bold]Due This Week:[/bold] {stats.due_this_week}",
        "",
        f"[bold]Current Streak:[/bold] [cyan]{stats.current_streak}[/cyan] days",
        f"[bold]Best Streak:[/bold] {stats.best_streak} days",
        "",
        f"[bold]Average EF:[/bold] {stats.average_easiness_factor}",
        f"[bold]Total Reviews:[/bold] {stats.total_reviews}",
    ]

    console.print(
        Panel(
            "\n".join(main_lines),
            title="[bold white]Statistics[/bold white]",
            border_style="green",
            box=box.ROUNDED,
        )
    )

    # Difficulty breakdown table
    table = Table(title="Difficulty Breakdown", box=box.SIMPLE)
    table.add_column("Difficulty", style="bold")
    table.add_column("Solved", justify="right", style="green")
    table.add_column("Total", justify="right")
    table.add_column("Progress", justify="left")

    difficulties = [
        ("Easy", stats.easy_solved, stats.easy_total, stats.easy_percentage, "green"),
        (
            "Medium",
            stats.medium_solved,
            stats.medium_total,
            stats.medium_percentage,
            "yellow",
        ),
        ("Hard", stats.hard_solved, stats.hard_total, stats.hard_percentage, "red"),
    ]

    for name, solved, total, pct, color in difficulties:
        # Create mini progress bar
        filled = int(pct / 10)
        bar = f"[{color}]{'█' * filled}[/{color}][dim]{'░' * (10 - filled)}[/dim]"
        table.add_row(
            f"[{color}]{name}[/{color}]",
            str(solved),
            str(total),
            f"{bar} {pct:.0f}%",
        )

    console.print()
    console.print(table)


def display_problem_list(
    problems: list[tuple[Problem, ProblemProgress | None]],
    show_url: bool = False,
) -> None:
    """Display a list of problems in a table.

    Args:
        problems: List of (Problem, ProblemProgress or None) tuples
        show_url: Whether to include URL column
    """
    if not problems:
        console.print("[yellow]No problems found.[/yellow]")
        return

    table = Table(title="Problems", box=box.SIMPLE)
    table.add_column("#", style="dim", width=4)
    table.add_column("Title", style="bold", max_width=40)
    table.add_column("Diff", justify="center", width=8)
    table.add_column("Category", max_width=25)
    table.add_column("Status", justify="center", width=10)
    table.add_column("EF", justify="right", width=5)

    if show_url:
        table.add_column("URL", max_width=30)

    for problem, progress in problems:
        diff_style = DIFFICULTY_STYLES.get(problem.difficulty, Style())

        if progress:
            if progress.solved:
                status = "[green]Solved[/green]"
            else:
                status = f"[yellow]{progress.attempts}x[/yellow]"
            ef = f"{progress.easiness_factor:.1f}"
        else:
            status = "[dim]New[/dim]"
            ef = "-"

        # Make title clickable
        title_link = make_link(str(problem.url), problem.title[:38])

        row = [
            str(problem.id or "-"),
            title_link,
            f"[{diff_style}]{problem.difficulty.value}[/]",
            problem.category[:23],
            status,
            ef,
        ]

        if show_url:
            row.append(str(problem.url)[:28])

        table.add_row(*row)

    console.print(table)


def display_session_summary(
    reviewed: int,
    total_due: int,
    qualities: list[int],
) -> None:
    """Display summary at end of review session.

    Args:
        reviewed: Number of problems reviewed
        total_due: Total that were due
        qualities: List of quality ratings given
    """
    console.print()

    if not qualities:
        console.print("[yellow]No problems reviewed.[/yellow]")
        return

    avg_quality = sum(qualities) / len(qualities)

    summary = [
        "[bold]Session Complete![/bold]",
        "",
        f"Problems reviewed: [cyan]{reviewed}[/cyan]/{total_due}",
        f"Average quality: [cyan]{avg_quality:.1f}[/cyan]/5",
    ]

    # Add encouragement based on performance
    if avg_quality >= 4:
        summary.append("")
        summary.append("[green]Excellent session! Keep up the great work![/green]")
    elif avg_quality >= 3:
        summary.append("")
        summary.append("[yellow]Good progress! Keep practicing.[/yellow]")
    else:
        summary.append("")
        summary.append(
            "[yellow]Some tough ones today. You'll get them next time![/yellow]"
        )

    console.print(
        Panel(
            "\n".join(summary),
            border_style="cyan",
            box=box.ROUNDED,
        )
    )


def display_success(message: str) -> None:
    """Display a success message."""
    console.print(f"[green]{message}[/green]")


def display_error(message: str) -> None:
    """Display an error message."""
    console.print(f"[red]Error: {message}[/red]")


def display_warning(message: str) -> None:
    """Display a warning message."""
    console.print(f"[yellow]Warning: {message}[/yellow]")


def display_info(message: str) -> None:
    """Display an info message."""
    console.print(f"[dim]{message}[/dim]")
