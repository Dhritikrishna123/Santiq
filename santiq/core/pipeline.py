"""Pipeline execution engine."""

import tempfile
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from santiq.core.audit import AuditLogger
from santiq.core.config import ConfigManager, PipelineConfig
from santiq.core.exceptions import PipelineExecutionError
from santiq.core.plugin_manager import PluginManager
from santiq.plugins.base.profiler import ProfileResult


class PipelineContext:
    """Holds pipeline execution context and state."""

    def __init__(self, pipeline_id: str, config: PipelineConfig) -> None:
        self.pipeline_id = pipeline_id
        self.config = config
        self.data: Optional[pd.DataFrame] = None
        self.profile_results: List[ProfileResult] = []
        self.applied_fixes: List[Dict[str, Any]] = []
        self.temp_dir: Optional[Path] = None

        if config.temp_dir:
            self.temp_dir = Path(config.temp_dir)
        else:
            self.temp_dir = Path(tempfile.mkdtemp(prefix="santiq_"))

    def cleanup(self) -> None:
        """Cleanup temporary resources."""
        if self.temp_dir and self.temp_dir.exists():
            import shutil

            shutil.rmtree(self.temp_dir)


class Pipeline:
    """Executes ETL pipelines with plugin orchestration."""

    def __init__(
        self,
        plugin_manager: PluginManager,
        audit_logger: AuditLogger,
        config_manager: ConfigManager,
    ) -> None:
        self.plugin_manager = plugin_manager
        self.audit_logger = audit_logger
        self.config_manager = config_manager

    def execute(
        self,
        config: PipelineConfig,
        mode: str = "manual",
        pipeline_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Execute a complete ETL pipeline."""
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
            context.data = self._execute_extraction(context)

            # Execute profiling
            if config.profilers:
                context.profile_results = self._execute_profiling(context)

            # Execute transformations
            if config.transformers:
                context.data = self._execute_transformations(context, mode)

            # Execute loading
            load_results = self._execute_loading(context)

            self.audit_logger.log_event(
                "pipeline_complete",
                pipeline_id,
                data={
                    "rows_processed": (
                        len(context.data) if context.data is not None else 0
                    ),
                    "fixes_applied": len(context.applied_fixes),
                    "load_results": load_results,
                },
            )

            return {
                "pipeline_id": pipeline_id,
                "success": True,
                "rows_processed": len(context.data) if context.data is not None else 0,
                "fixes_applied": context.applied_fixes,
                "load_results": load_results,
                "data": context.data,
            }

        except Exception as e:
            self.audit_logger.log_event(
                "pipeline_error", pipeline_id, success=False, error_message=str(e)
            )
            raise PipelineExecutionError("pipeline", e)

        finally:
            context.cleanup()

    def _execute_extraction(self, context: PipelineContext) -> pd.DataFrame:
        """Execute the extraction stage."""
        config = context.config.extractor

        try:
            extractor = self.plugin_manager.create_plugin_instance(
                config.plugin, "extractor", config.params
            )

            self.audit_logger.log_event(
                "plugin_start",
                context.pipeline_id,
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
                context.pipeline_id,
                stage="extract",
                plugin_name=config.plugin,
                plugin_type="extractor",
                data={"rows_extracted": len(data), "columns": list(data.columns)},
            )

            return data

        except Exception as e:
            self.audit_logger.log_event(
                "plugin_error",
                context.pipeline_id,
                stage="extract",
                plugin_name=config.plugin,
                plugin_type="extractor",
                success=False,
                error_message=str(e),
            )
            raise
        finally:
            self.plugin_manager.cleanup_plugin_instance(config.plugin, "extractor")

    def _execute_profiling(self, context: PipelineContext) -> List[ProfileResult]:
        """Execute profiling plugins."""
        results = []

        for profiler_config in context.config.profilers:
            if not profiler_config.enabled:
                continue

            try:
                profiler = self.plugin_manager.create_plugin_instance(
                    profiler_config.plugin, "profiler", profiler_config.params
                )

                self.audit_logger.log_event(
                    "plugin_start",
                    context.pipeline_id,
                    stage="profile",
                    plugin_name=profiler_config.plugin,
                    plugin_type="profiler",
                )

                # Ensure the profiler has the profile method
                if not hasattr(profiler, "profile") or not callable(profiler.profile):
                    raise AttributeError(
                        f"Plugin {profiler_config.plugin} does not have a callable 'profile' method"
                    )

                result = profiler.profile(context.data)
                results.append(result)

                self.audit_logger.log_event(
                    "plugin_complete",
                    context.pipeline_id,
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
                    context.pipeline_id,
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

    def _execute_transformations(
        self, context: PipelineContext, mode: str
    ) -> pd.DataFrame:
        """Execute transformation plugins."""
        current_data = (
            context.data.copy() if context.data is not None else pd.DataFrame()
        )

        for transformer_config in context.config.transformers:
            if not transformer_config.enabled:
                continue

            try:
                transformer = self.plugin_manager.create_plugin_instance(
                    transformer_config.plugin, "transformer", transformer_config.params
                )

                self.audit_logger.log_event(
                    "plugin_start",
                    context.pipeline_id,
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
                    # Type assertion since we know this is a transformer plugin
                    from santiq.plugins.base.transformer import TransformerPlugin

                    transformer_plugin = transformer  # type: ignore[assignment]
                    suggestions = transformer_plugin.suggest_fixes(  # type: ignore[union-attr]
                        current_data, self._get_relevant_issues(context.profile_results)
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
                context.applied_fixes.extend(result.applied_fixes)

                self.audit_logger.log_event(
                    "plugin_complete",
                    context.pipeline_id,
                    stage="transform",
                    plugin_name=transformer_config.plugin,
                    plugin_type="transformer",
                    data={
                        "rows_before": (
                            len(context.data) if context.data is not None else 0
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
                    context.pipeline_id,
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

    def _execute_loading(self, context: PipelineContext) -> List[Dict[str, Any]]:
        """Execute loader plugins."""
        results = []

        for loader_config in context.config.loaders:
            if not loader_config.enabled:
                continue

            try:
                loader = self.plugin_manager.create_plugin_instance(
                    loader_config.plugin, "loader", loader_config.params
                )

                self.audit_logger.log_event(
                    "plugin_start",
                    context.pipeline_id,
                    stage="load",
                    plugin_name=loader_config.plugin,
                    plugin_type="loader",
                )

                # Ensure the loader has the load method
                if not hasattr(loader, "load") or not callable(loader.load):
                    raise AttributeError(
                        f"Plugin {loader_config.plugin} does not have a callable 'load' method"
                    )

                result = loader.load(context.data)
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
                    context.pipeline_id,
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
                    context.pipeline_id,
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
        """Extract all issues from profiling results."""
        all_issues = []
        for result in profile_results:
            all_issues.extend(result.issues)
        return all_issues

    def _get_user_approval(
        self, suggestions: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Get user approval for suggestions (placeholder for CLI/UI interaction)."""
        # This would be implemented with actual user interaction
        # For now, return all suggestions as approved
        return suggestions

    def _auto_approve_known_fixes(
        self, suggestions: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Auto-approve fixes based on stored preferences."""
        preferences = self.config_manager.load_preferences()
        approved = []

        for suggestion in suggestions:
            fix_type = suggestion.get("fix_type", "unknown")
            if preferences.get(f"auto_approve.{fix_type}", False):
                approved.append(suggestion)

        return approved
