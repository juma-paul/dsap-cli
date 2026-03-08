"""
Tests for Configuration Management

These tests verify the ConfigManager correctly loads, saves,
and manages user configuration.
"""

import json
from pathlib import Path

import pytest

from dsap.config import ConfigManager
from dsap.models import Difficulty


class TestConfigManager:
    """Tests for ConfigManager class."""

    @pytest.fixture
    def temp_config_path(self, tmp_path: Path) -> Path:
        """Create a temporary config file path."""
        return tmp_path / "config.json"

    @pytest.fixture
    def config_manager(self, temp_config_path: Path) -> ConfigManager:
        """Create a ConfigManager with temporary path."""
        return ConfigManager(path=temp_config_path)

    def test_load_creates_default_config(self, config_manager: ConfigManager):
        """Loading non-existent config returns defaults."""
        config = config_manager.load()
        assert config.daily_goal == 5
        assert config.show_hints is True
        assert config.auto_open_browser is True

    def test_save_creates_file(
        self,
        config_manager: ConfigManager,
        temp_config_path: Path,
    ):
        """Saving config creates the file."""
        config_manager.load()
        config_manager.save()
        assert temp_config_path.exists()

    def test_save_and_load_roundtrip(
        self,
        config_manager: ConfigManager,
        temp_config_path: Path,
    ):
        """Config survives save/load cycle."""
        config_manager.load()
        config_manager.set("daily_goal", 10)
        config_manager.set("show_hints", False)
        config_manager.save()

        # Create new manager and load
        new_manager = ConfigManager(path=temp_config_path)
        config = new_manager.load()

        assert config.daily_goal == 10
        assert config.show_hints is False

    def test_get_returns_value(self, config_manager: ConfigManager):
        """get() returns configuration value."""
        assert config_manager.get("daily_goal") == 5
        assert config_manager.get("show_hints") is True

    def test_get_unknown_key_returns_none(self, config_manager: ConfigManager):
        """get() returns None for unknown keys."""
        assert config_manager.get("nonexistent_key") is None

    def test_set_updates_value(self, config_manager: ConfigManager):
        """set() updates configuration value."""
        config_manager.set("daily_goal", 15)
        assert config_manager.get("daily_goal") == 15

    def test_set_converts_string_to_int(self, config_manager: ConfigManager):
        """set() converts string daily_goal to int."""
        config_manager.set("daily_goal", "20")
        assert config_manager.get("daily_goal") == 20

    def test_set_converts_bool_strings(self, config_manager: ConfigManager):
        """set() converts string booleans."""
        config_manager.set("show_hints", "false")
        assert config_manager.get("show_hints") is False

        config_manager.set("show_hints", "true")
        assert config_manager.get("show_hints") is True

        config_manager.set("auto_open_browser", "no")
        assert config_manager.get("auto_open_browser") is False

        config_manager.set("auto_open_browser", "yes")
        assert config_manager.get("auto_open_browser") is True

    def test_set_difficulty(self, config_manager: ConfigManager):
        """set() handles preferred_difficulty."""
        config_manager.set("preferred_difficulty", "Medium")
        assert config_manager.get("preferred_difficulty") == Difficulty.MEDIUM

    def test_set_difficulty_none(self, config_manager: ConfigManager):
        """set() handles preferred_difficulty = None."""
        config_manager.set("preferred_difficulty", "Medium")
        config_manager.set("preferred_difficulty", "none")
        assert config_manager.get("preferred_difficulty") is None

    def test_set_unknown_key_raises(self, config_manager: ConfigManager):
        """set() raises ValueError for unknown keys."""
        with pytest.raises(ValueError, match="Unknown configuration key"):
            config_manager.set("unknown_key", "value")

    def test_all_returns_dict(self, config_manager: ConfigManager):
        """all() returns all config as dict."""
        config = config_manager.all()
        assert isinstance(config, dict)
        assert "daily_goal" in config
        assert "show_hints" in config
        assert "auto_open_browser" in config

    def test_reset_restores_defaults(self, config_manager: ConfigManager):
        """reset() restores default values."""
        config_manager.set("daily_goal", 50)
        config_manager.set("show_hints", False)

        config_manager.reset()

        assert config_manager.get("daily_goal") == 5
        assert config_manager.get("show_hints") is True

    def test_load_invalid_json_returns_defaults(
        self,
        temp_config_path: Path,
    ):
        """Loading invalid JSON returns defaults."""
        temp_config_path.parent.mkdir(parents=True, exist_ok=True)
        temp_config_path.write_text("{ invalid json }")

        manager = ConfigManager(path=temp_config_path)
        config = manager.load()

        assert config.daily_goal == 5  # Default value

    def test_load_caches_config(self, config_manager: ConfigManager):
        """load() caches the config object."""
        config1 = config_manager.load()
        config2 = config_manager.load()
        assert config1 is config2

    def test_save_converts_difficulty_to_string(
        self,
        config_manager: ConfigManager,
        temp_config_path: Path,
    ):
        """save() converts Difficulty enum to string for JSON."""
        config_manager.set("preferred_difficulty", "Hard")
        config_manager.save()

        # Read raw JSON
        with open(temp_config_path) as f:
            data = json.load(f)

        assert data["preferred_difficulty"] == "Hard"

    def test_ensures_directory_exists(self, tmp_path: Path):
        """save() creates parent directories if needed."""
        deep_path = tmp_path / "a" / "b" / "c" / "config.json"
        manager = ConfigManager(path=deep_path)

        manager.load()
        manager.save()

        assert deep_path.exists()
