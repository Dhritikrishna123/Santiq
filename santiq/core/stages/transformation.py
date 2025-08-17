"""Transformation stage for pipeline execution."""

from typing import Any, Dict, List

import pandas as pd

from santiq.core.pipeline_context import PipelineContext
from santiq.core.stages.base import BaseStage
from santiq.plugins.base.profiler import ProfileResult


class TransformationStage(BaseStage):
    """Handles execution of the transformation stage.

    This stage is responsible for cleaning and transforming data
    using configured transformer plugins.
    """

    def execute(
        self, context: PipelineContext, mode: str = "manual", **kwargs: Any
    ) -> pd.DataFrame:
        """Execute the transformation stage.

        Args:
            context: Pipeline context containing configuration and state
            mode: Execution mode (manual, half-auto, controlled-auto)
            **kwargs: Additional arguments (not used in transformation)

        Returns:
            Transformed data as DataFrame

        Raises:
            Exception: If transformation fails and on_error is set to "stop"
        """
        current_data = (
            context.get_data().copy()
            if context.get_data() is not None
            else pd.DataFrame()
        )
        pipeline_id = context.get_pipeline_id()

        for transformer_config in context.get_config().transformers:
            if not transformer_config.enabled:
                continue

            try:
                # Create transformer plugin instance
                transformer = self.plugin_manager.create_plugin_instance(
                    transformer_config.plugin, "transformer", transformer_config.params
                )

                # Log plugin start
                self._log_plugin_start(
                    pipeline_id, "transform", transformer_config.plugin, "transformer"
                )

                # Validate transformer has required methods
                self._validate_plugin_method(
                    transformer, "transform", transformer_config.plugin
                )
                self._validate_plugin_method(
                    transformer, "suggest_fixes", transformer_config.plugin
                )

                # Get suggestions if in interactive mode
                approved_suggestions = self._get_approved_suggestions(
                    transformer, current_data, context, mode
                )

                # Execute transformation
                result = transformer.transform(current_data)
                current_data = result.data

                # Add applied fixes to context
                for fix in result.applied_fixes:
                    context.add_applied_fix(fix)

                # Log successful completion
                self._log_plugin_complete(
                    pipeline_id,
                    "transform",
                    transformer_config.plugin,
                    "transformer",
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
                # Handle errors based on configuration
                if transformer_config.on_error == "stop":
                    self._log_plugin_error(
                        pipeline_id,
                        "transform",
                        transformer_config.plugin,
                        "transformer",
                        str(e),
                    )
                    raise

                # Log error but continue with other transformers
                self._log_plugin_error(
                    pipeline_id,
                    "transform",
                    transformer_config.plugin,
                    "transformer",
                    str(e),
                )
            finally:
                # Cleanup plugin instance
                self._cleanup_plugin(transformer_config.plugin, "transformer", context)

        return current_data

    def _get_approved_suggestions(
        self,
        transformer: Any,
        data: pd.DataFrame,
        context: PipelineContext,
        mode: str,
    ) -> List[Dict[str, Any]]:
        """Get approved suggestions based on execution mode.

        Args:
            transformer: Transformer plugin instance
            data: Current data to transform
            context: Pipeline context
            mode: Execution mode

        Returns:
            List of approved suggestions
        """
        if mode in ["manual", "half-auto"]:
            # Get suggestions from transformer
            suggestions = transformer.suggest_fixes(
                data, self._get_relevant_issues(context.get_profile_results())
            )

            if mode == "manual":
                # In manual mode, user would review suggestions via CLI/UI
                return self._get_user_approval(suggestions)
            else:  # half-auto
                return self._auto_approve_known_fixes(suggestions)
        else:  # controlled-auto
            return self._auto_approve_known_fixes([])

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
