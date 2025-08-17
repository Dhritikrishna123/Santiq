"""Profiling stage for pipeline execution."""

from typing import Any, List

from santiq.core.pipeline_context import PipelineContext
from santiq.core.stages.base import BaseStage
from santiq.plugins.base.profiler import ProfileResult


class ProfilingStage(BaseStage):
    """Handles execution of the profiling stage.

    This stage is responsible for analyzing data quality and identifying
    issues using configured profiler plugins.
    """

    def execute(self, context: PipelineContext, **kwargs: Any) -> List[ProfileResult]:
        """Execute the profiling stage.

        Args:
            context: Pipeline context containing configuration and state
            **kwargs: Additional arguments (not used in profiling)

        Returns:
            List of profile results from all enabled profilers

        Raises:
            Exception: If profiling fails and on_error is set to "stop"
        """
        results = []
        pipeline_id = context.get_pipeline_id()

        for profiler_config in context.get_config().profilers:
            if not profiler_config.enabled:
                continue

            try:
                # Create profiler plugin instance
                profiler = self.plugin_manager.create_plugin_instance(
                    profiler_config.plugin, "profiler", profiler_config.params
                )

                # Log plugin start
                self._log_plugin_start(
                    pipeline_id, "profile", profiler_config.plugin, "profiler"
                )

                # Validate profiler has required method
                self._validate_plugin_method(
                    profiler, "profile", profiler_config.plugin
                )

                # Execute profiling
                result = profiler.profile(context.get_data())
                results.append(result)
                context.add_profile_result(result)

                # Log successful completion
                self._log_plugin_complete(
                    pipeline_id,
                    "profile",
                    profiler_config.plugin,
                    "profiler",
                    data={
                        "issues_found": len(result.issues),
                        "suggestions": len(result.suggestions),
                    },
                )

            except Exception as e:
                # Handle errors based on configuration
                if profiler_config.on_error == "stop":
                    self._log_plugin_error(
                        pipeline_id,
                        "profile",
                        profiler_config.plugin,
                        "profiler",
                        str(e),
                    )
                    raise

                # Log error but continue with other profilers
                self._log_plugin_error(
                    pipeline_id,
                    "profile",
                    profiler_config.plugin,
                    "profiler",
                    str(e),
                )
            finally:
                # Cleanup plugin instance
                self._cleanup_plugin(profiler_config.plugin, "profiler", context)

        return results
