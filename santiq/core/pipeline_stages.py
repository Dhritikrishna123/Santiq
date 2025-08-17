"""Pipeline stage execution functionality."""

from typing import Any, Dict, List

import pandas as pd

from santiq.core.audit import AuditLogger
from santiq.core.pipeline_context import PipelineContext
from santiq.core.plugin_manager import PluginManager
from santiq.plugins.base.profiler import ProfileResult


class PipelineStages:
    """Handles execution of individual pipeline stages."""

    def __init__(
        self, plugin_manager: PluginManager, audit_logger: AuditLogger
    ) -> None:
        """Initialize pipeline stages.

        Args:
            plugin_manager: Plugin manager instance
            audit_logger: Audit logger instance
        """
        self.plugin_manager = plugin_manager
        self.audit_logger = audit_logger

    def execute_extraction(self, context: PipelineContext) -> pd.DataFrame:
        """Execute the extraction stage.

        Args:
            context: Pipeline context

        Returns:
            Extracted data as DataFrame
        """
        config = context.get_config().extractor

        try:
            extractor = self.plugin_manager.create_plugin_instance(
                config.plugin, "extractor", config.params
            )

            self.audit_logger.log_event(
                "plugin_start",
                context.get_pipeline_id(),
                stage="extract",
                plugin_name=config.plugin,
                plugin_type="extractor",
            )

            # Ensure the extractor has the extract method
            if not hasattr(extractor, "extract") or not callable(extractor.extract):
                raise AttributeError(
                    f"Plugin {config.plugin} does not have a callable 'extract' method"
                )

            data = extractor.extract()

            self.audit_logger.log_event(
                "plugin_complete",
                context.get_pipeline_id(),
                stage="extract",
                plugin_name=config.plugin,
                plugin_type="extractor",
                data={"rows_extracted": len(data), "columns": list(data.columns)},
            )

            return data

        except Exception as e:
            self.audit_logger.log_event(
                "plugin_error",
                context.get_pipeline_id(),
                stage="extract",
                plugin_name=config.plugin,
                plugin_type="extractor",
                success=False,
                error_message=str(e),
            )
            raise
        finally:
            self.plugin_manager.cleanup_plugin_instance(config.plugin, "extractor")

    def execute_profiling(self, context: PipelineContext) -> List[ProfileResult]:
        """Execute profiling plugins.

        Args:
            context: Pipeline context

        Returns:
            List of profile results
        """
        results = []

        for profiler_config in context.get_config().profilers:
            if not profiler_config.enabled:
                continue

            try:
                profiler = self.plugin_manager.create_plugin_instance(
                    profiler_config.plugin, "profiler", profiler_config.params
                )

                self.audit_logger.log_event(
                    "plugin_start",
                    context.get_pipeline_id(),
                    stage="profile",
                    plugin_name=profiler_config.plugin,
                    plugin_type="profiler",
                )

                # Ensure the profiler has the profile method
                if not hasattr(profiler, "profile") or not callable(profiler.profile):
                    raise AttributeError(
                        f"Plugin {profiler_config.plugin} does not have a callable 'profile' method"
                    )

                result = profiler.profile(context.get_data())
                results.append(result)
                context.add_profile_result(result)

                self.audit_logger.log_event(
                    "plugin_complete",
                    context.get_pipeline_id(),
                    stage="profile",
                    plugin_name=profiler_config.plugin,
                    plugin_type="profiler",
                    data={
                        "issues_found": len(result.issues),
                        "suggestions": len(result.suggestions),
                    },
                )

            except Exception as e:
                if profiler_config.on_error == "stop":
                    raise

                self.audit_logger.log_event(
                    "plugin_error",
                    context.get_pipeline_id(),
                    stage="profile",
                    plugin_name=profiler_config.plugin,
                    plugin_type="profiler",
                    success=False,
                    error_message=str(e),
                )
            finally:
                self.plugin_manager.cleanup_plugin_instance(
                    profiler_config.plugin, "profiler"
                )

        return results

    def execute_transformations(
        self, context: PipelineContext, mode: str
    ) -> pd.DataFrame:
        """Execute transformation plugins.

        Args:
            context: Pipeline context
            mode: Execution mode (manual, half-auto, controlled-auto)

        Returns:
            Transformed data as DataFrame
        """
        current_data = (
            context.get_data().copy()
            if context.get_data() is not None
            else pd.DataFrame()
        )

        for transformer_config in context.get_config().transformers:
            if not transformer_config.enabled:
                continue

            try:
                transformer = self.plugin_manager.create_plugin_instance(
                    transformer_config.plugin, "transformer", transformer_config.params
                )

                self.audit_logger.log_event(
                    "plugin_start",
                    context.get_pipeline_id(),
                    stage="transform",
                    plugin_name=transformer_config.plugin,
                    plugin_type="transformer",
                )

                # Ensure the transformer has the required methods
                if not hasattr(transformer, "transform") or not callable(
                    transformer.transform
                ):
                    raise AttributeError(
                        f"Plugin {transformer_config.plugin} does not have a callable 'transform' method"
                    )

                if not hasattr(transformer, "suggest_fixes") or not callable(
                    transformer.suggest_fixes
                ):
                    raise AttributeError(
                        f"Plugin {transformer_config.plugin} does not have a callable 'suggest_fixes' method"
                    )

                # Get suggestions if in interactive mode
                if mode in ["manual", "half-auto"]:
                    suggestions = transformer.suggest_fixes(
                        current_data,
                        self._get_relevant_issues(context.get_profile_results()),
                    )
                    if mode == "manual":
                        # In manual mode, user would review suggestions via CLI/UI
                        approved_suggestions = self._get_user_approval(suggestions)
                    else:  # half-auto
                        approved_suggestions = self._auto_approve_known_fixes(
                            suggestions
                        )
                else:  # controlled-auto
                    approved_suggestions = self._auto_approve_known_fixes([])

                result = transformer.transform(current_data)
                current_data = result.data

                # Add applied fixes to context
                for fix in result.applied_fixes:
                    context.add_applied_fix(fix)

                self.audit_logger.log_event(
                    "plugin_complete",
                    context.get_pipeline_id(),
                    stage="transform",
                    plugin_name=transformer_config.plugin,
                    plugin_type="transformer",
                    data={
                        "rows_before": (
                            len(context.get_data())
                            if context.get_data() is not None
                            else 0
                        ),
                        "rows_after": len(current_data),
                        "fixes_applied": len(result.applied_fixes),
                    },
                )

            except Exception as e:
                if transformer_config.on_error == "stop":
                    raise

                self.audit_logger.log_event(
                    "plugin_error",
                    context.get_pipeline_id(),
                    stage="transform",
                    plugin_name=transformer_config.plugin,
                    plugin_type="transformer",
                    success=False,
                    error_message=str(e),
                )
            finally:
                self.plugin_manager.cleanup_plugin_instance(
                    transformer_config.plugin, "transformer"
                )

        return current_data

    def execute_loading(self, context: PipelineContext) -> List[Dict[str, Any]]:
        """Execute loader plugins.

        Args:
            context: Pipeline context

        Returns:
            List of load results
        """
        results = []

        for loader_config in context.get_config().loaders:
            if not loader_config.enabled:
                continue

            try:
                loader = self.plugin_manager.create_plugin_instance(
                    loader_config.plugin, "loader", loader_config.params
                )

                self.audit_logger.log_event(
                    "plugin_start",
                    context.get_pipeline_id(),
                    stage="load",
                    plugin_name=loader_config.plugin,
                    plugin_type="loader",
                )

                # Ensure the loader has the load method
                if not hasattr(loader, "load") or not callable(loader.load):
                    raise AttributeError(
                        f"Plugin {loader_config.plugin} does not have a callable 'load' method"
                    )

                result = loader.load(context.get_data())
                results.append(
                    {
                        "plugin": loader_config.plugin,
                        "success": result.success,
                        "rows_loaded": result.rows_loaded,
                        "metadata": result.metadata,
                    }
                )

                self.audit_logger.log_event(
                    "plugin_complete",
                    context.get_pipeline_id(),
                    stage="load",
                    plugin_name=loader_config.plugin,
                    plugin_type="loader",
                    data={"rows_loaded": result.rows_loaded},
                )

            except Exception as e:
                if loader_config.on_error == "stop":
                    raise

                results.append(
                    {"plugin": loader_config.plugin, "success": False, "error": str(e)}
                )

                self.audit_logger.log_event(
                    "plugin_error",
                    context.get_pipeline_id(),
                    stage="load",
                    plugin_name=loader_config.plugin,
                    plugin_type="loader",
                    success=False,
                    error_message=str(e),
                )
            finally:
                self.plugin_manager.cleanup_plugin_instance(
                    loader_config.plugin, "loader"
                )

        return results

    def _get_relevant_issues(
        self, profile_results: List[ProfileResult]
    ) -> List[Dict[str, Any]]:
        """Extract all issues from profiling results.

        Args:
            profile_results: List of profile results

        Returns:
            List of all issues found
        """
        all_issues = []
        for result in profile_results:
            all_issues.extend(result.issues)
        return all_issues

    def _get_user_approval(
        self, suggestions: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Get user approval for suggestions (placeholder for CLI/UI interaction).

        Args:
            suggestions: List of suggestions to approve

        Returns:
            List of approved suggestions
        """
        # This would be implemented with actual user interaction
        # For now, return all suggestions as approved
        return suggestions

    def _auto_approve_known_fixes(
        self, suggestions: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Auto-approve fixes based on stored preferences.

        Args:
            suggestions: List of suggestions to auto-approve

        Returns:
            List of auto-approved suggestions
        """
        # This would load preferences from config manager
        # For now, return empty list (no auto-approval)
        return []
