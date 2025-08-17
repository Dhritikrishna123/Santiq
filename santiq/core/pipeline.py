"""Pipeline execution engine."""

import uuid
from typing import Any, Dict, Optional

from santiq.core.audit import AuditLogger
from santiq.core.config import ConfigManager, PipelineConfig
from santiq.core.exceptions import PipelineExecutionError
from santiq.core.pipeline_context import PipelineContext
from santiq.core.stages import PipelineStages
from santiq.core.plugin_manager import PluginManager


class Pipeline:
    """Executes ETL pipelines with plugin orchestration."""

    def __init__(
        self,
        plugin_manager: PluginManager,
        audit_logger: AuditLogger,
        config_manager: ConfigManager,
    ) -> None:
        """Initialize pipeline.

        Args:
            plugin_manager: Plugin manager instance
            audit_logger: Audit logger instance
            config_manager: Configuration manager instance
        """
        self.plugin_manager = plugin_manager
        self.audit_logger = audit_logger
        self.config_manager = config_manager
        self.stages = PipelineStages(plugin_manager, audit_logger)

    def execute(
        self,
        config: PipelineConfig,
        mode: str = "manual",
        pipeline_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Execute a complete ETL pipeline.

        Args:
            config: Pipeline configuration
            mode: Execution mode (manual, half-auto, controlled-auto)
            pipeline_id: Optional pipeline ID, will generate if not provided

        Returns:
            Pipeline execution results

        Raises:
            PipelineExecutionError: If pipeline execution fails
        """
        if pipeline_id is None:
            pipeline_id = str(uuid.uuid4())

        context = PipelineContext(pipeline_id, config)

        try:
            self.audit_logger.log_event(
                "pipeline_start",
                pipeline_id,
                data={"mode": mode, "config": config.model_dump()},
            )

            # Execute extraction
            data = self.stages.execute_extraction(context)
            context.set_data(data)

            # Execute profiling
            if config.profilers:
                self.stages.execute_profiling(context)

            # Execute transformations
            if config.transformers:
                transformed_data = self.stages.execute_transformations(context, mode)
                context.set_data(transformed_data)

            # Execute loading
            load_results = self.stages.execute_loading(context)

            self.audit_logger.log_event(
                "pipeline_complete",
                pipeline_id,
                data={
                    "rows_processed": (
                        len(context.get_data()) if context.get_data() is not None else 0
                    ),
                    "fixes_applied": len(context.get_applied_fixes()),
                    "load_results": load_results,
                },
            )

            return {
                "pipeline_id": pipeline_id,
                "success": True,
                "rows_processed": len(context.get_data()) if context.get_data() is not None else 0,
                "fixes_applied": context.get_applied_fixes(),
                "load_results": load_results,
                "data": context.get_data(),
            }

        except Exception as e:
            self.audit_logger.log_event(
                "pipeline_error", pipeline_id, success=False, error_message=str(e)
            )
            raise PipelineExecutionError("pipeline", e)

        finally:
            context.cleanup()
