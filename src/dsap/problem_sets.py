"""Problem Set Loader for DSAP.

Handles loading problems from:
- Bundled YAML files (Blind 75, NeetCode 150, Grind 75)
- Custom user YAML files
"""

import logging
from importlib import resources
from pathlib import Path
from typing import Any

import yaml

from dsap.models import Difficulty, Problem

logger = logging.getLogger(__name__)


# Bundled problem sets
BUNDLED_SETS: dict[str, str] = {
    "blind75": "blind75.yaml",
    "neetcode150": "neetcode150.yaml",
    "grind75": "grind75.yaml",
}

# Descriptions for listing
SET_DESCRIPTIONS: dict[str, str] = {
    "blind75": "Blind 75 - The essential 75 LeetCode problems",
    "neetcode150": "NeetCode 150 - Extended curated problem set",
    "grind75": "Grind 75 - Flexible 75-question study plan",
}


def list_bundled_sets() -> dict[str, str]:
    """List available bundled problem sets.

    Returns:
        Dict mapping set name to description
    """
    return SET_DESCRIPTIONS.copy()


def get_bundled_path(set_name: str) -> Path:
    """Get the path to a bundled problem set file.

    Args:
        set_name: Name of the set (e.g., "blind75")

    Returns:
        Path to the YAML file

    Raises:
        ValueError: If set_name is not a valid bundled set
    """
    if set_name not in BUNDLED_SETS:
        available = ", ".join(BUNDLED_SETS.keys())
        raise ValueError(f"Unknown problem set: '{set_name}'. Available: {available}")

    try:
        files = resources.files("dsap.data")
        path = files.joinpath(BUNDLED_SETS[set_name])

        with resources.as_file(path) as p:
            return Path(p)
    except (TypeError, AttributeError):
        data_dir = Path(__file__).parent / "data"
        return data_dir / BUNDLED_SETS[set_name]


def load_problem_set(source: str) -> list[Problem]:
    """Load problems from a YAML file or bundled set name.

    Args:
        source: Either a bundled set name (e.g., "blind75")
               or a path to a custom YAML file

    Returns:
        List of Problem objects

    Raises:
        ValueError: If source is not valid
        FileNotFoundError: If file doesn't exist
    """
    # Check if it's a bundled set name
    if source.lower() in BUNDLED_SETS:
        path = get_bundled_path(source.lower())
    else:
        path = Path(source)

    if not path.exists():
        raise FileNotFoundError(f"Problem set file not found: {path}")

    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    return parse_problem_set(data)


def parse_problem_set(data: dict[str, Any]) -> list[Problem]:
    """Parse YAML data structure into Problem objects.

    Expected YAML structure:
    ```yaml
    metadata:
      name: "Set Name"
      description: "Description"
    categories:
      - name: "Category Name"
        problems:
          - title: "Problem Title"
            url: "https://..."
            difficulty: "Easy"
            ...
    ```

    Args:
        data: Parsed YAML data

    Returns:
        List of Problem objects
    """
    problems: list[Problem] = []

    # Get metadata
    metadata = data.get("metadata", {})
    set_name = metadata.get("name", "custom")

    # Track problem number across all categories
    problem_number = 1

    # Parse each category
    for category in data.get("categories", []):
        category_name = category.get("name", "Uncategorized")

        for prob_data in category.get("problems", []):
            try:
                problem = Problem(
                    title=prob_data["title"],
                    url=prob_data["url"],
                    difficulty=Difficulty.from_string(prob_data["difficulty"]),
                    category=category_name,
                    description=prob_data.get("description", ""),
                    tags=prob_data.get("tags", []),
                    problem_set=set_name,
                    problem_number=problem_number,
                    company_tags=prob_data.get("company_tags", []),
                    hints=prob_data.get("hints", []),
                )
                problems.append(problem)
                problem_number += 1
            except (KeyError, ValueError, TypeError) as e:
                title = prob_data.get("title", "Unknown")
                logger.warning("Failed to parse problem '%s': %s", title, e)

    return problems


def create_custom_set(
    name: str,
    problems: list[dict[str, Any]],
    output_path: Path,
) -> None:
    """Create a custom problem set YAML file.

    Args:
        name: Name of the problem set
        problems: List of problem dictionaries
        output_path: Where to save the YAML file
    """
    # Group problems by category
    by_category: dict[str, list[dict[str, Any]]] = {}
    for prob in problems:
        cat = prob.get("category", "Custom")
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(prob)

    # Build YAML structure
    data = {
        "metadata": {
            "name": name,
            "description": f"Custom problem set: {name}",
            "total_problems": len(problems),
        },
        "categories": [
            {"name": cat, "problems": probs} for cat, probs in by_category.items()
        ],
    }

    # Write to file
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)
