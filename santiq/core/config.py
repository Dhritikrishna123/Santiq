"""Configuration management for the Santiq platform."""

import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator

from santiq.core.exceptions import PipelineConfigError


class PluginConfig(BaseModel):
    """Configuration for a single plugin"""

    model_config = ConfigDict(extra="forbid")

    plugin: str = Field(..., min_length=1, description="Plugin name/identifier")
    params: Dict[str, Any] = Field(
        default_factory=dict, description="Plugin parameters"
    )
    on_error: str = Field(
        default="stop",
        pattern="^(stop|continue|retry)$",
        description="Error handling strategy",
    )
    enabled: bool = Field(default=True, description="Whether the plugin is enabled")
    timeout: Optional[int] = Field(
        default=None, gt=0, description="Plugin timeout in seconds"
    )

    @field_validator("plugin")
    @classmethod
    def validate_plugin_name(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Plugin name cannot be empty or whitespace")
        return v.strip()


class PipelineConfig(BaseModel):
    """Configuration for a data processing pipeline"""

    model_config = ConfigDict(extra="forbid")

    name: Optional[str] = Field(default=None, description="Pipeline name")
    description: Optional[str] = Field(default=None, description="Pipeline description")
    version: Optional[str] = Field(default="1.0.0", description="Pipeline version")

    extractor: PluginConfig = Field(..., description="Data extraction plugin")
    profilers: List[PluginConfig] = Field(
        default_factory=list, description="Data profiling plugins"
    )
    transformers: List[PluginConfig] = Field(
        default_factory=list, description="Data transformation plugins"
    )
    loaders: List[PluginConfig] = Field(..., description="Data loading plugins")

    # Global settings
    cache_intermediate_results: bool = Field(
        default=True, description="Whether to cache intermediate results"
    )
    max_memory_mb: Optional[int] = Field(
        default=None, gt=0, description="Maximum memory usage in MB"
    )
    temp_dir: Optional[str] = Field(
        default=None, description="Temporary directory path"
    )
    parallel_execution: bool = Field(
        default=False, description="Enable parallel execution where possible"
    )
    log_level: str = Field(
        default="INFO",
        pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$",
        description="Logging level",
    )

    @field_validator("loaders")
    @classmethod
    def validate_loaders_not_empty(cls, v: List[PluginConfig]) -> List[PluginConfig]:
        if not v:
            raise ValueError("At least one loader must be specified")
        return v

    @field_validator("temp_dir")
    @classmethod
    def validate_temp_dir(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            temp_path = Path(v).expanduser().resolve()
            if not temp_path.exists():
                try:
                    temp_path.mkdir(parents=True, exist_ok=True)
                except (OSError, PermissionError) as e:
                    raise ValueError(f"Cannot create temporary directory {v}: {e}")
            elif not temp_path.is_dir():
                raise ValueError(
                    f"Temporary directory path {v} exists but is not a directory"
                )
        return v

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError("Pipeline name cannot be empty or whitespace only")
        return v.strip() if v else None


class ConfigManager:
    """Manages configuration loading and environment variable substitution"""

    def __init__(self, config_search_paths: Optional[List[str]] = None):
        """
        Initialize ConfigManager with optional search paths for configuration files.

        Args:
            config_search_paths: List of directories to search for configuration files
        """
        self.env_pattern = re.compile(r"\$\{([^}]+)\}")
        self.config_search_paths = config_search_paths or []
        self._add_default_search_paths()

    def _add_default_search_paths(self) -> None:
        """Add default configuration search paths"""
        default_paths = [
            os.getcwd(),  # Current working directory
            os.path.expanduser("~/.santiq"),  # User config directory
        ]

        # Add system config directory only on Unix-like systems
        if os.name == "posix":
            default_paths.append("/etc/santiq")  # System config directory (Unix-like)
        elif os.name == "nt":  # Windows
            # Add Windows-specific config paths if needed
            windows_config = os.path.expanduser("~/AppData/Local/santiq")
            if os.path.exists(windows_config):
                default_paths.append(windows_config)

        for path in default_paths:
            if path not in self.config_search_paths:
                self.config_search_paths.append(path)

    def find_config_file(self, config_filename: str) -> Optional[str]:
        """
        Find a configuration file in the search paths.

        Args:
            config_filename: Name of the configuration file

        Returns:
            Full path to the configuration file if found, None otherwise
        """
        for search_path in self.config_search_paths:
            config_path = Path(search_path) / config_filename
            if config_path.exists() and config_path.is_file():
                return str(config_path)
        return None

    def load_pipeline_config(self, config_path: str) -> PipelineConfig:
        """
        Load and validate pipeline configuration from file.

        Args:
            config_path: Path to the configuration file

        Returns:
            PipelineConfig object

        Raises:
            PipelineConfigError: If configuration cannot be loaded or is invalid
        """
        # Try to find config file if it's just a filename
        if not os.path.sep in config_path and not Path(config_path).exists():
            found_path = self.find_config_file(config_path)
            if found_path:
                config_path = found_path

        config_file = Path(config_path)
        if not config_file.exists():
            raise PipelineConfigError(f"Configuration file not found: {config_path}")

        if not config_file.is_file():
            raise PipelineConfigError(
                f"Configuration path is not a file: {config_path}"
            )

        try:
            with open(config_file, "r", encoding="utf-8") as f:
                raw_config = yaml.safe_load(f)

            if raw_config is None:
                raise PipelineConfigError(f"Configuration file is empty: {config_path}")

            # Substitute environment variables
            processed_config = self._substitute_env_vars(raw_config)

            # Validate and create config object
            return PipelineConfig(**processed_config)

        except yaml.YAMLError as e:
            raise PipelineConfigError(
                f"Error parsing YAML configuration file {config_path}: {e}"
            )
        except FileNotFoundError:
            raise PipelineConfigError(f"Configuration file not found: {config_path}")
        except PermissionError:
            raise PipelineConfigError(
                f"Permission denied reading configuration file: {config_path}"
            )
        except Exception as e:
            raise PipelineConfigError(
                f"Unexpected error loading configuration file {config_path}: {e}"
            )

    def _substitute_env_vars(self, obj: Any) -> Any:
        """
        Recursively substitute environment variables in the config object.

        Args:
            obj: Configuration object (dict, list, str, or other)

        Returns:
            Object with environment variables substituted
        """
        if isinstance(obj, dict):
            return {key: self._substitute_env_vars(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._substitute_env_vars(item) for item in obj]
        elif isinstance(obj, str):
            return self._substitute_string_env_vars(obj)
        else:
            return obj

    def _substitute_string_env_vars(self, text: str) -> str:
        """
        Substitute environment variables in a string using ${VAR} or ${VAR:default} syntax.

        Args:
            text: String potentially containing environment variable references

        Returns:
            String with environment variables substituted
        """

        def replace_var(match: re.Match[str]) -> str:
            var_spec = match.group(1)

            # Support ${VAR:default} syntax
            if ":" in var_spec:
                var_name, default_value = var_spec.split(":", 1)
            else:
                var_name, default_value = var_spec, ""

            # Clean up variable name
            var_name = var_name.strip()

            return os.getenv(var_name, default_value)

        return self.env_pattern.sub(replace_var, text)

    def save_preferences(
        self, preferences: Dict[str, Any], preference_file: Optional[str] = None
    ) -> None:
        """
        Save user preferences to file.

        Args:
            preferences: Dictionary of preferences to save
            preference_file: Optional path to preference file

        Raises:
            PipelineConfigError: If preferences cannot be saved
        """
        if preference_file is None:
            preference_file = self._get_default_preference_file()

        preference_path = Path(preference_file)

        # Create parent directories if they don't exist
        try:
            preference_path.parent.mkdir(parents=True, exist_ok=True)
        except (OSError, PermissionError) as e:
            raise PipelineConfigError(
                f"Cannot create preference directory {preference_path.parent}: {e}"
            )

        try:
            with open(preference_path, "w", encoding="utf-8") as f:
                yaml.dump(
                    preferences, f, default_flow_style=False, sort_keys=True, indent=2
                )
        except (OSError, PermissionError) as e:
            raise PipelineConfigError(
                f"Permission denied writing preferences to {preference_file}: {e}"
            )
        except Exception as e:
            raise PipelineConfigError(
                f"Error saving preferences to {preference_file}: {e}"
            )

    def load_preferences(self, preference_file: Optional[str] = None) -> Dict[str, Any]:
        """
        Load user preferences from file.

        Args:
            preference_file: Optional path to preference file

        Returns:
            Dictionary of preferences, empty dict if file doesn't exist

        Raises:
            PipelineConfigError: If preferences cannot be loaded
        """
        if preference_file is None:
            preference_file = self._get_default_preference_file()

        preference_path = Path(preference_file)
        if not preference_path.exists():
            return {}

        try:
            with open(preference_path, "r", encoding="utf-8") as f:
                preferences = yaml.safe_load(f)
                return preferences if preferences is not None else {}
        except yaml.YAMLError as e:
            raise PipelineConfigError(
                f"Error parsing preference file {preference_file}: {e}"
            )
        except (OSError, PermissionError) as e:
            raise PipelineConfigError(
                f"Error reading preference file {preference_file}: {e}"
            )
        except Exception as e:
            raise PipelineConfigError(
                f"Unexpected error loading preferences from {preference_file}: {e}"
            )

    def _get_default_preference_file(self) -> str:
        """
        Get the default preference file path based on the operating system.

        Returns:
            Path to the default preference file
        """
        if os.name == "nt":  # Windows
            config_dir = os.getenv("APPDATA", os.path.expanduser("~"))
        else:  # Unix-like systems
            config_dir = os.getenv("XDG_CONFIG_HOME", os.path.expanduser("~/.config"))

        return os.path.join(config_dir, "santiq", "preferences.yml")

    def validate_config_schema(self, config_dict: Dict[str, Any]) -> bool:
        """
        Validate configuration dictionary against the schema without creating the object.

        Args:
            config_dict: Configuration dictionary to validate

        Returns:
            True if valid, raises exception if invalid

        Raises:
            PipelineConfigError: If configuration is invalid
        """
        try:
            PipelineConfig(**config_dict)
            return True
        except Exception as e:
            raise PipelineConfigError(f"Configuration validation failed: {e}")

    def merge_configs(
        self, base_config: Dict[str, Any], override_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Merge two configuration dictionaries, with override_config taking precedence.

        Args:
            base_config: Base configuration dictionary
            override_config: Override configuration dictionary

        Returns:
            Merged configuration dictionary
        """

        def deep_merge(
            base: Dict[str, Any], override: Dict[str, Any]
        ) -> Dict[str, Any]:
            merged = base.copy()
            for key, value in override.items():
                if (
                    key in merged
                    and isinstance(merged[key], dict)
                    and isinstance(value, dict)
                ):
                    merged[key] = deep_merge(merged[key], value)
                else:
                    merged[key] = value
            return merged

        return deep_merge(base_config, override_config)
