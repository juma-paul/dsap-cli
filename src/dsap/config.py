"""Configuration Management for DSAP.

Handles user preferences stored in ~/.dsap/config.json.
"""

import json
from pathlib import Path
from typing import Any

from dsap.models import Config as ConfigModel
from dsap.models import Difficulty


class ConfigManager:
    """Manages user configuration for DSAP.

    Configuration is stored in ~/.dsap/config.json and includes
    settings like daily goals, preferred difficulty, etc.
    """

    DEFAULT_PATH = Path.home() / ".dsap" / "config.json"

    def __init__(self, path: Path | None = None):
        """Initialize config manager.

        Args:
            path: Optional custom path to config file.
                 Defaults to ~/.dsap/config.json
        """
        self.path = path or self.DEFAULT_PATH
        self._config: ConfigModel | None = None

    def _ensure_directory(self) -> None:
        """Ensure the config directory exists."""
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def load(self) -> ConfigModel:
        """Load configuration from file.

        Returns default config if file doesn't exist.
        """
        if self._config is not None:
            return self._config

        if not self.path.exists():
            self._config = ConfigModel()
            return self._config

        try:
            with open(self.path, encoding="utf-8") as f:
                data = json.load(f)
            self._config = ConfigModel(**data)
        except (json.JSONDecodeError, OSError, TypeError, ValueError):
            # Invalid config file or read error, use defaults
            self._config = ConfigModel()

        return self._config

    def save(self) -> None:
        """Save current configuration to file."""
        if self._config is None:
            return

        self._ensure_directory()

        data = self._config.model_dump()

        # Convert Difficulty enum to string for JSON
        if data.get("preferred_difficulty"):
            data["preferred_difficulty"] = data["preferred_difficulty"].value

        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def get(self, key: str) -> Any:
        """Get a configuration value.

        Args:
            key: Configuration key

        Returns:
            Configuration value or None if not found
        """
        config = self.load()
        return getattr(config, key, None)

    def set(self, key: str, value: Any) -> None:
        """Set a configuration value.

        Args:
            key: Configuration key
            value: Value to set
        """
        config = self.load()

        # Handle special cases
        if key == "preferred_difficulty" and isinstance(value, str):
            if value.lower() == "none":
                value = None
            else:
                value = Difficulty.from_string(value)

        if key == "preferred_set" and isinstance(value, str):
            if value.lower() == "none":
                value = None
            # Normalize set names
            elif value.lower() in ("blind75", "blind 75"):
                value = "Blind 75"
            elif value.lower() in ("neetcode150", "neetcode 150"):
                value = "NeetCode 150"
            elif value.lower() in ("grind75", "grind 75"):
                value = "Grind 75"

        if key == "daily_goal":
            value = int(value)

        if key == "show_hints":
            if isinstance(value, str):
                value = value.lower() in ("true", "yes", "1", "on")

        if key == "auto_open_browser":
            if isinstance(value, str):
                value = value.lower() in ("true", "yes", "1", "on")

        if hasattr(config, key):
            setattr(config, key, value)
            self._config = config
            self.save()
        else:
            raise ValueError(f"Unknown configuration key: {key}")

    def all(self) -> dict[str, Any]:
        """Get all configuration as a dictionary."""
        config = self.load()
        data = config.model_dump()

        # Convert enum to string for display
        if data.get("preferred_difficulty"):
            data["preferred_difficulty"] = data["preferred_difficulty"].value

        return data

    def reset(self) -> None:
        """Reset configuration to defaults."""
        self._config = ConfigModel()
        self.save()


# Global config instance
_config_manager: ConfigManager | None = None


def get_config() -> ConfigManager:
    """Get the global config manager instance."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager
