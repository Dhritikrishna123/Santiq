"""Loading stage for pipeline execution."""

from typing import Any, Dict, List

from santiq.core.pipeline_context import PipelineContext
from santiq.core.stages.base import BaseStage


class LoadingStage(BaseStage):
    """Handles execution of the loading stage.

    This stage is responsible for loading data to various destinations
    using configured loader plugins.
    """

    def execute(self, context: PipelineContext, **kwargs: Any) -> List[Dict[str, Any]]:
        """Execute the loading stage.

        Args:
            context: Pipeline context containing configuration and state
            **kwargs: Additional arguments (not used in loading)

        Returns:
            List of load results from all enabled loaders

        Raises:
            Exception: If loading fails and on_error is set to "stop"
        """
        results = []
        pipeline_id = context.get_pipeline_id()

        for loader_config in context.get_config().loaders:
            if not loader_config.enabled:
                continue

            try:
                # Create loader plugin instance
                loader = self.plugin_manager.create_plugin_instance(
                    loader_config.plugin, "loader", loader_config.params
                )

                # Log plugin start
                self._log_plugin_start(
                    pipeline_id, "load", loader_config.plugin, "loader"
                )

                # Validate loader has required method
                self._validate_plugin_method(loader, "load", loader_config.plugin)

                # Execute loading
                result = loader.load(context.get_data())
                results.append(
                    {
                        "plugin": loader_config.plugin,
                        "success": result.success,
                        "rows_loaded": result.rows_loaded,
                        "metadata": result.metadata,
                    }
                )

                # Log successful completion
                self._log_plugin_complete(
                    pipeline_id,
                    "load",
                    loader_config.plugin,
                    "loader",
                    data={"rows_loaded": result.rows_loaded},
                )

            except Exception as e:
                # Handle errors based on configuration
                if loader_config.on_error == "stop":
                    self._log_plugin_error(
                        pipeline_id,
                        "load",
                        loader_config.plugin,
                        "loader",
                        str(e),
                    )
                    raise

                # Log error and add to results
                results.append(
                    {"plugin": loader_config.plugin, "success": False, "error": str(e)}
                )

                self._log_plugin_error(
                    pipeline_id,
                    "load",
                    loader_config.plugin,
                    "loader",
                    str(e),
                )
            finally:
                # Cleanup plugin instance
                self._cleanup_plugin(loader_config.plugin, "loader", context)

        return results
