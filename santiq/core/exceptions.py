"""Custom exceptions for the Santiq platform.

This module defines a hierarchy of custom exceptions used throughout
the Santiq ETL platform. All exceptions inherit from SantiqError,
which provides a common base for error handling and identification.
"""

from typing import Any, Optional


class SantiqError(Exception):
    """Base class for all Santiq exceptions.

    This exception serves as the root of the exception hierarchy
    for the Santiq platform. All custom exceptions should inherit
    from this class to enable consistent error handling.
    """

    pass


class PluginError(SantiqError):
    """Base exception for all plugin-related errors.

    This exception is raised when there are issues with plugin
    discovery, loading, validation, or execution.
    """

    pass


class PluginNotFoundError(PluginError):
    """Raised when a requested plugin cannot be found.

    This exception is raised when the system attempts to load
    a plugin that doesn't exist or isn't available.

    Attributes:
        plugin_name: Name of the plugin that was not found
        plugin_type: Type of plugin (extractor, profiler, transformer, loader)
    """

    def __init__(self, plugin_name: str, plugin_type: str) -> None:
        """Initialize the exception.

        Args:
            plugin_name: Name of the plugin that was not found
            plugin_type: Type of plugin (extractor, profiler, transformer, loader)
        """
        self.plugin_name = plugin_name
        self.plugin_type = plugin_type
        super().__init__(f"Plugin '{plugin_name}' of type '{plugin_type}' not found")


class PluginLoadError(PluginError):
    """Raised when a plugin fails to load or initialize.

    This exception is raised when a plugin exists but cannot be
    properly loaded due to import errors, missing dependencies,
    or other loading issues.

    Attributes:
        plugin_name: Name of the plugin that failed to load
        error: The underlying exception that caused the load failure
    """

    def __init__(self, plugin_name: str, error: Exception) -> None:
        """Initialize the exception.

        Args:
            plugin_name: Name of the plugin that failed to load
            error: The underlying exception that caused the load failure
        """
        self.plugin_name = plugin_name
        self.error = error
        super().__init__(f"Failed to load plugin '{plugin_name}': {error}")


class PluginVersionError(PluginError):
    """Raised when a plugin's API version is incompatible.

    This exception is raised when a plugin requires a different
    API version than what the platform currently supports.

    Attributes:
        plugin_name: Name of the plugin with version incompatibility
        required: The API version required by the plugin
        found: The API version currently supported by the platform
    """

    def __init__(self, plugin_name: str, required: str, found: str) -> None:
        """Initialize the exception.

        Args:
            plugin_name: Name of the plugin with version incompatibility
            required: The API version required by the plugin
            found: The API version currently supported by the platform
        """
        self.plugin_name = plugin_name
        self.required = required
        self.found = found
        super().__init__(
            f"Plugin '{plugin_name}' requires API version {required}, but found {found}"
        )


class PipelineError(SantiqError):
    """Base exception for all pipeline-related errors.

    This exception is raised when there are issues with pipeline
    configuration, execution, or data processing.
    """

    pass


class PipelineConfigError(PipelineError):
    """Raised when there is a configuration error in the pipeline.

    This exception is raised when the pipeline configuration is
    invalid, missing required fields, or contains unsupported values.
    """

    pass


class PipelineExecutionError(PipelineError):
    """Raised when there is an error during pipeline execution.

    This exception is raised when a pipeline stage fails to execute
    properly, such as when a plugin throws an exception or when
    data processing fails.

    Attributes:
        stage: The pipeline stage where the error occurred
        error: The underlying exception that caused the failure
    """

    def __init__(self, stage: str, error: Exception) -> None:
        """Initialize the exception.

        Args:
            stage: The pipeline stage where the error occurred
            error: The underlying exception that caused the failure
        """
        self.stage = stage
        self.error = error
        super().__init__(f"Error occurred in stage '{stage}': {error}")


class DataValidationError(SantiqError):
    """Raised when data validation fails.

    This exception is raised when data doesn't meet the expected
    format, schema, or quality requirements.

    Attributes:
        message: Description of the validation error
        data_info: Additional information about the data that failed validation
    """

    def __init__(
        self, message: str, data_info: Optional[dict[str, Any]] = None
    ) -> None:
        """Initialize the exception.

        Args:
            message: Description of the validation error
            data_info: Additional information about the data that failed validation
        """
        self.message = message
        self.data_info = data_info or {}
        super().__init__(message)


class ETLError(Exception):
    """Legacy exception for backward compatibility.

    This exception is maintained for backward compatibility with
    existing code. New code should use the more specific exceptions
    defined above.
    """

    pass
