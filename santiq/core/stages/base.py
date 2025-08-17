"""Base stage class for pipeline execution."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

import pandas as pd

from santiq.core.audit import AuditLogger
from santiq.core.plugin_manager import PluginManager
from santiq.core.pipeline_context import PipelineContext


class BaseStage(ABC):
    """Base class for all pipeline stages.

    This class provides common functionality for executing pipeline stages,
    including plugin management, audit logging, and error handling.
    """

    def __init__(self, plugin_manager: PluginManager, audit_logger: AuditLogger) -> None:
        """Initialize the base stage.

        Args:
            plugin_manager: Plugin manager instance for creating plugin instances
            audit_logger: Audit logger instance for logging events
        """
        self.plugin_manager = plugin_manager
        self.audit_logger = audit_logger

    def _log_plugin_start(
        self,
        pipeline_id: str,
        stage: str,
        plugin_name: str,
        plugin_type: str,
        **kwargs: Any,
    ) -> None:
        """Log the start of a plugin execution.

        Args:
            pipeline_id: Unique identifier for the pipeline
            stage: Current pipeline stage (extract, profile, transform, load)
            plugin_name: Name of the plugin being executed
            plugin_type: Type of plugin (extractor, profiler, transformer, loader)
            **kwargs: Additional data to log
        """
        self.audit_logger.log_event(
            "plugin_start",
            pipeline_id,
            stage=stage,
            plugin_name=plugin_name,
            plugin_type=plugin_type,
            **kwargs,
        )

    def _log_plugin_complete(
        self,
        pipeline_id: str,
        stage: str,
        plugin_name: str,
        plugin_type: str,
        data: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """Log the successful completion of a plugin execution.

        Args:
            pipeline_id: Unique identifier for the pipeline
            stage: Current pipeline stage (extract, profile, transform, load)
            plugin_name: Name of the plugin that completed
            plugin_type: Type of plugin (extractor, profiler, transformer, loader)
            data: Additional data to log about the execution
            **kwargs: Additional data to log
        """
        self.audit_logger.log_event(
            "plugin_complete",
            pipeline_id,
            stage=stage,
            plugin_name=plugin_name,
            plugin_type=plugin_type,
            data=data,
            **kwargs,
        )

    def _log_plugin_error(
        self,
        pipeline_id: str,
        stage: str,
        plugin_name: str,
        plugin_type: str,
        error_message: str,
        **kwargs: Any,
    ) -> None:
        """Log an error during plugin execution.

        Args:
            pipeline_id: Unique identifier for the pipeline
            stage: Current pipeline stage (extract, profile, transform, load)
            plugin_name: Name of the plugin that encountered an error
            plugin_type: Type of plugin (extractor, profiler, transformer, loader)
            error_message: Description of the error that occurred
            **kwargs: Additional data to log
        """
        self.audit_logger.log_event(
            "plugin_error",
            pipeline_id,
            stage=stage,
            plugin_name=plugin_name,
            plugin_type=plugin_type,
            success=False,
            error_message=error_message,
            **kwargs,
        )

    def _validate_plugin_method(
        self, plugin_instance: Any, method_name: str, plugin_name: str
    ) -> None:
        """Validate that a plugin instance has a required method.

        Args:
            plugin_instance: The plugin instance to validate
            method_name: Name of the method that should exist
            plugin_name: Name of the plugin for error messages

        Raises:
            AttributeError: If the plugin doesn't have the required method
        """
        if not hasattr(plugin_instance, method_name) or not callable(
            getattr(plugin_instance, method_name)
        ):
            raise AttributeError(
                f"Plugin {plugin_name} does not have a callable '{method_name}' method"
            )

    def _cleanup_plugin(
        self, plugin_name: str, plugin_type: str, context: PipelineContext
    ) -> None:
        """Clean up a plugin instance after execution.

        Args:
            plugin_name: Name of the plugin to clean up
            plugin_type: Type of plugin (extractor, profiler, transformer, loader)
            context: Pipeline context for additional cleanup if needed
        """
        try:
            self.plugin_manager.cleanup_plugin_instance(plugin_name, plugin_type)
        except Exception as e:
            # Log cleanup errors but don't raise them
            self._log_plugin_error(
                context.get_pipeline_id(),
                "cleanup",
                plugin_name,
                plugin_type,
                f"Failed to cleanup plugin: {e}",
            )

    @abstractmethod
    def execute(self, context: PipelineContext, **kwargs: Any) -> Any:
        """Execute the pipeline stage.

        Args:
            context: Pipeline context containing configuration and state
            **kwargs: Additional arguments specific to the stage

        Returns:
            Stage-specific result (DataFrame, list of results, etc.)
        """
        pass
