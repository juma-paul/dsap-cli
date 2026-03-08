"""
Tests for Problem Set Loader

These tests verify the YAML problem set loading and parsing
functionality.
"""

from pathlib import Path

import pytest

from dsap.models import Difficulty
from dsap.problem_sets import (
    BUNDLED_SETS,
    create_custom_set,
    list_bundled_sets,
    load_problem_set,
    parse_problem_set,
)


class TestBundledSets:
    """Tests for bundled problem set functionality."""

    def test_list_bundled_sets(self):
        """list_bundled_sets returns descriptions."""
        sets = list_bundled_sets()
        assert "blind75" in sets
        assert "Blind 75" in sets["blind75"]

    def test_bundled_sets_exist(self):
        """All bundled sets have corresponding files."""
        assert "blind75" in BUNDLED_SETS
        assert BUNDLED_SETS["blind75"] == "blind75.yaml"

    def test_load_blind75(self):
        """Load the Blind 75 problem set."""
        problems = load_problem_set("blind75")
        assert len(problems) > 0
        assert problems[0].problem_set == "Blind 75"

    def test_load_case_insensitive(self):
        """Bundled set names are case insensitive."""
        problems1 = load_problem_set("blind75")
        problems2 = load_problem_set("BLIND75")
        problems3 = load_problem_set("Blind75")

        assert len(problems1) == len(problems2) == len(problems3)


class TestParseProblemSet:
    """Tests for parse_problem_set function."""

    def test_parse_minimal(self):
        """Parse minimal valid YAML structure."""
        data = {
            "metadata": {"name": "Test Set"},
            "categories": [
                {
                    "name": "Arrays",
                    "problems": [
                        {
                            "title": "Two Sum",
                            "url": "https://leetcode.com/problems/two-sum/",
                            "difficulty": "Easy",
                        }
                    ],
                }
            ],
        }

        problems = parse_problem_set(data)
        assert len(problems) == 1
        assert problems[0].title == "Two Sum"
        assert problems[0].difficulty == Difficulty.EASY
        assert problems[0].category == "Arrays"
        assert problems[0].problem_set == "Test Set"
        assert problems[0].problem_number == 1

    def test_parse_multiple_categories(self):
        """Parse multiple categories with correct numbering."""
        data = {
            "metadata": {"name": "Multi Category"},
            "categories": [
                {
                    "name": "Arrays",
                    "problems": [
                        {
                            "title": "Problem 1",
                            "url": "https://example.com/1",
                            "difficulty": "Easy",
                        },
                        {
                            "title": "Problem 2",
                            "url": "https://example.com/2",
                            "difficulty": "Medium",
                        },
                    ],
                },
                {
                    "name": "Trees",
                    "problems": [
                        {
                            "title": "Problem 3",
                            "url": "https://example.com/3",
                            "difficulty": "Hard",
                        },
                    ],
                },
            ],
        }

        problems = parse_problem_set(data)
        assert len(problems) == 3
        assert problems[0].problem_number == 1
        assert problems[1].problem_number == 2
        assert problems[2].problem_number == 3
        assert problems[0].category == "Arrays"
        assert problems[2].category == "Trees"

    def test_parse_with_optional_fields(self):
        """Parse problems with optional fields."""
        data = {
            "metadata": {"name": "Full"},
            "categories": [
                {
                    "name": "Arrays",
                    "problems": [
                        {
                            "title": "Two Sum",
                            "url": "https://leetcode.com/problems/two-sum/",
                            "difficulty": "Easy",
                            "description": "Find two numbers",
                            "tags": ["array", "hash-table"],
                            "company_tags": ["Google", "Amazon"],
                            "hints": ["Use a hash map"],
                        }
                    ],
                }
            ],
        }

        problems = parse_problem_set(data)
        problem = problems[0]
        assert problem.description == "Find two numbers"
        assert "array" in problem.tags
        assert "Google" in problem.company_tags
        assert "Use a hash map" in problem.hints

    def test_parse_default_metadata(self):
        """Missing metadata uses defaults."""
        data = {
            "categories": [
                {
                    "name": "Test",
                    "problems": [
                        {
                            "title": "Test",
                            "url": "https://example.com/test",
                            "difficulty": "Easy",
                        }
                    ],
                }
            ],
        }

        problems = parse_problem_set(data)
        assert problems[0].problem_set == "custom"

    def test_parse_empty_categories(self):
        """Empty categories list returns empty."""
        data = {"metadata": {"name": "Empty"}, "categories": []}
        problems = parse_problem_set(data)
        assert problems == []

    def test_parse_skips_invalid_problems(self, caplog):
        """Invalid problems are skipped with warning."""
        import logging

        data = {
            "metadata": {"name": "Mixed"},
            "categories": [
                {
                    "name": "Test",
                    "problems": [
                        {
                            "title": "Valid",
                            "url": "https://example.com/valid",
                            "difficulty": "Easy",
                        },
                        {
                            "title": "Invalid",
                            "url": "not-a-url",  # Invalid URL
                            "difficulty": "Easy",
                        },
                    ],
                }
            ],
        }

        with caplog.at_level(logging.WARNING):
            problems = parse_problem_set(data)

        assert len(problems) == 1
        assert problems[0].title == "Valid"

        # Check warning was logged
        assert "Invalid" in caplog.text


class TestLoadProblemSet:
    """Tests for load_problem_set function."""

    def test_load_custom_file(self, tmp_path: Path):
        """Load problems from custom YAML file."""
        yaml_content = """
metadata:
  name: "Custom Set"
categories:
  - name: "Test Category"
    problems:
      - title: "Custom Problem"
        url: "https://example.com/custom"
        difficulty: "Medium"
"""
        yaml_file = tmp_path / "custom.yaml"
        yaml_file.write_text(yaml_content)

        problems = load_problem_set(str(yaml_file))
        assert len(problems) == 1
        assert problems[0].title == "Custom Problem"
        assert problems[0].problem_set == "Custom Set"

    def test_load_nonexistent_file_raises(self):
        """Loading non-existent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_problem_set("/nonexistent/path/file.yaml")


class TestCreateCustomSet:
    """Tests for create_custom_set function."""

    def test_create_custom_set(self, tmp_path: Path):
        """Create a custom problem set YAML file."""
        problems = [
            {
                "title": "Problem 1",
                "url": "https://example.com/1",
                "difficulty": "Easy",
                "category": "Arrays",
            },
            {
                "title": "Problem 2",
                "url": "https://example.com/2",
                "difficulty": "Medium",
                "category": "Trees",
            },
        ]

        output = tmp_path / "output.yaml"
        create_custom_set("My Set", problems, output)

        assert output.exists()

        # Load and verify
        loaded = load_problem_set(str(output))
        assert len(loaded) == 2

    def test_create_custom_set_groups_by_category(self, tmp_path: Path):
        """Problems are grouped by category."""
        problems = [
            {
                "title": "Array 1",
                "url": "https://example.com/a1",
                "difficulty": "Easy",
                "category": "Arrays",
            },
            {
                "title": "Array 2",
                "url": "https://example.com/a2",
                "difficulty": "Easy",
                "category": "Arrays",
            },
            {
                "title": "Tree 1",
                "url": "https://example.com/t1",
                "difficulty": "Medium",
                "category": "Trees",
            },
        ]

        output = tmp_path / "grouped.yaml"
        create_custom_set("Grouped", problems, output)

        # Read and check structure
        import yaml

        with open(output) as f:
            data = yaml.safe_load(f)

        assert len(data["categories"]) == 2
        categories = {c["name"]: c for c in data["categories"]}
        assert len(categories["Arrays"]["problems"]) == 2
        assert len(categories["Trees"]["problems"]) == 1

    def test_create_custom_set_creates_directories(self, tmp_path: Path):
        """Parent directories are created if needed."""
        output = tmp_path / "a" / "b" / "c" / "set.yaml"
        create_custom_set("Nested", [], output)
        assert output.exists()
