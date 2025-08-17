"""Main pipeline stages orchestrator."""

from typing import Any, Dict, List

import pandas as pd

from santiq.core.audit import AuditLogger
from santiq.core.pipeline_context import PipelineContext
from santiq.core.plugin_manager import PluginManager
from santiq.core.stages.extraction import ExtractionStage
from santiq.core.stages.loading import LoadingStage
from santiq.core.stages.profiling import ProfilingStage
from santiq.core.stages.transformation import TransformationStage
from santiq.plugins.base.profiler import ProfileResult


class PipelineStages:
    """Orchestrates execution of individual pipeline stages.

    This class coordinates the execution of all pipeline stages:
    - Extraction: Extract data from various sources
    - Profiling: Analyze data quality and identify issues
    - Transformation: Clean and transform data
    - Loading: Load data to various destinations

    Each stage is handled by a dedicated stage class that inherits from BaseStage.
    """

    def __init__(
        self, plugin_manager: PluginManager, audit_logger: AuditLogger
    ) -> None:
        """Initialize the pipeline stages orchestrator.

        Args:
            plugin_manager: Plugin manager instance for creating plugin instances
            audit_logger: Audit logger instance for logging events
        """
        self.plugin_manager = plugin_manager
        self.audit_logger = audit_logger

        # Initialize individual stage handlers
        self.extraction_stage = ExtractionStage(plugin_manager, audit_logger)
        self.profiling_stage = ProfilingStage(plugin_manager, audit_logger)
        self.transformation_stage = TransformationStage(plugin_manager, audit_logger)
        self.loading_stage = LoadingStage(plugin_manager, audit_logger)

    def execute_extraction(self, context: PipelineContext) -> pd.DataFrame:
        """Execute the extraction stage.

        Args:
            context: Pipeline context containing configuration and state

        Returns:
            Extracted data as DataFrame

        Raises:
            Exception: If extraction fails
        """
        return self.extraction_stage.execute(context)

    def execute_profiling(self, context: PipelineContext) -> List[ProfileResult]:
        """Execute the profiling stage.

        Args:
            context: Pipeline context containing configuration and state

        Returns:
            List of profile results from all enabled profilers

        Raises:
            Exception: If profiling fails and on_error is set to "stop"
        """
        return self.profiling_stage.execute(context)

    def execute_transformations(
        self, context: PipelineContext, mode: str
    ) -> pd.DataFrame:
        """Execute the transformation stage.

        Args:
            context: Pipeline context containing configuration and state
            mode: Execution mode (manual, half-auto, controlled-auto)

        Returns:
            Transformed data as DataFrame

        Raises:
            Exception: If transformation fails and on_error is set to "stop"
        """
        return self.transformation_stage.execute(context, mode=mode)

    def execute_loading(self, context: PipelineContext) -> List[Dict[str, Any]]:
        """Execute the loading stage.

        Args:
            context: Pipeline context containing configuration and state

        Returns:
            List of load results from all enabled loaders

        Raises:
            Exception: If loading fails and on_error is set to "stop"
        """
        return self.loading_stage.execute(context)
