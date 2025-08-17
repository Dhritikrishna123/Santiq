"""Extraction stage for pipeline execution."""

from typing import Any

import pandas as pd

from santiq.core.pipeline_context import PipelineContext
from santiq.core.stages.base import BaseStage


class ExtractionStage(BaseStage):
    """Handles execution of the extraction stage.

    This stage is responsible for extracting data from various sources
    using configured extractor plugins.
    """

    def execute(self, context: PipelineContext, **kwargs: Any) -> pd.DataFrame:
        """Execute the extraction stage.

        Args:
            context: Pipeline context containing configuration and state
            **kwargs: Additional arguments (not used in extraction)

        Returns:
            Extracted data as DataFrame

        Raises:
            Exception: If extraction fails
        """
        config = context.get_config().extractor
        pipeline_id = context.get_pipeline_id()

        try:
            # Create extractor plugin instance
            extractor = self.plugin_manager.create_plugin_instance(
                config.plugin, "extractor", config.params
            )

            # Log plugin start
            self._log_plugin_start(pipeline_id, "extract", config.plugin, "extractor")

            # Validate extractor has required method
            self._validate_plugin_method(extractor, "extract", config.plugin)

            # Execute extraction
            data = extractor.extract()

            # Log successful completion
            self._log_plugin_complete(
                pipeline_id,
                "extract",
                config.plugin,
                "extractor",
                data={
                    "rows_extracted": len(data),
                    "columns": list(data.columns),
                },
            )

            return data

        except Exception as e:
            # Log error
            self._log_plugin_error(
                pipeline_id, "extract", config.plugin, "extractor", str(e)
            )
            raise
        finally:
            # Cleanup plugin instance
            self._cleanup_plugin(config.plugin, "extractor", context)
