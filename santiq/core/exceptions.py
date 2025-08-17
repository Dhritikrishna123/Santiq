"""Custom exceptions for the Santiq platform."""

from typing import Any, Optional


class SantiqError(Exception):
    """Base class for all Santiq exceptions."""

    pass


class PluginError(SantiqError):
    """Exception raised for errors related to plugins."""

    pass


class PluginNotFoundError(PluginError):
    """Raised when a plugin cannot be found"""

    def __init__(self, plugin_name: str, plugin_type: str) -> None:
        self.plugin_name = plugin_name
        self.plugin_type = plugin_type
        super().__init__(f"Plugin '{plugin_name}' of type '{plugin_type}' not found")


class PluginLoadError(PluginError):
    """Raised when a plugin fails to load."""

    def __init__(self, plugin_name: str, error: Exception) -> None:
        self.plugin_name = plugin_name
        self.error = error
        super().__init__(f"Failed to load plugin '{plugin_name}': {error}")


class PluginVersionError(PluginError):
    """Raised when Plugin Api Version is incompatible"""

    def __init__(self, plugin_name: str, required: str, found: str) -> None:
        self.plugin_name = plugin_name
        self.required = required
        self.found = found
        super().__init__(
            f"Plugin '{plugin_name}' requires API version {required}, but found {found}"
        )


class PipelineError(SantiqError):
    """Base Exception for pipeline related errors"""

    pass


class PipelineConfigError(PipelineError):
    """Raised when there is a configuration error in the pipeline."""

    pass


class PipelineExecutionError(PipelineError):
    """Raised when there is an error during pipeline execution."""

    def __init__(self, stage: str, error: Exception) -> None:
        self.stage = stage
        self.error = error
        super().__init__(f"Error occurred in stage '{stage}': {error}")


class DataValidationError(SantiqError):
    """Raised when data validation fails."""

    def __init__(
        self, message: str, data_info: Optional[dict[str, Any]] = None
    ) -> None:
        self.message = message
        self.data_info = data_info or {}
        super().__init__(message)


class ETLError(Exception):
    pass
