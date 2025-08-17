"""Configuration models for the Santiq platform."""

from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


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
        """Validate plugin name is not empty or whitespace.

        Args:
            v: Plugin name to validate

        Returns:
            Validated plugin name

        Raises:
            ValueError: If plugin name is empty or whitespace
        """
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
        """Validate that at least one loader is specified.

        Args:
            v: List of loader configurations

        Returns:
            Validated list of loader configurations

        Raises:
            ValueError: If no loaders are specified
        """
        if not v:
            raise ValueError("At least one loader must be specified")
        return v

    @field_validator("temp_dir")
    @classmethod
    def validate_temp_dir(cls, v: Optional[str]) -> Optional[str]:
        """Validate temporary directory path.

        Args:
            v: Temporary directory path

        Returns:
            Validated temporary directory path

        Raises:
            ValueError: If temporary directory cannot be created or is invalid
        """
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
        """Validate pipeline name is not empty or whitespace.

        Args:
            v: Pipeline name to validate

        Returns:
            Validated pipeline name

        Raises:
            ValueError: If pipeline name is empty or whitespace
        """
        if v is not None and not v.strip():
            raise ValueError("Pipeline name cannot be empty or whitespace only")
        return v.strip() if v else None
