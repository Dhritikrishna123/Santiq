"""Pipeline context management functionality."""

import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from santiq.core.config import PipelineConfig
from santiq.plugins.base.profiler import ProfileResult


class PipelineContext:
    """Holds pipeline execution context and state."""

    def __init__(self, pipeline_id: str, config: PipelineConfig) -> None:
        """Initialize pipeline context.

        Args:
            pipeline_id: Unique identifier for the pipeline execution
            config: Pipeline configuration
        """
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

    def set_data(self, data: pd.DataFrame) -> None:
        """Set the current data in the context.

        Args:
            data: DataFrame to set as current data
        """
        self.data = data

    def get_data(self) -> Optional[pd.DataFrame]:
        """Get the current data from the context.

        Returns:
            Current DataFrame or None if not set
        """
        return self.data

    def add_profile_result(self, result: ProfileResult) -> None:
        """Add a profile result to the context.

        Args:
            result: Profile result to add
        """
        self.profile_results.append(result)

    def get_profile_results(self) -> List[ProfileResult]:
        """Get all profile results from the context.

        Returns:
            List of profile results
        """
        return self.profile_results

    def add_applied_fix(self, fix: Dict[str, Any]) -> None:
        """Add an applied fix to the context.

        Args:
            fix: Fix information to add
        """
        self.applied_fixes.append(fix)

    def get_applied_fixes(self) -> List[Dict[str, Any]]:
        """Get all applied fixes from the context.

        Returns:
            List of applied fixes
        """
        return self.applied_fixes

    def get_temp_dir(self) -> Path:
        """Get the temporary directory for this pipeline execution.

        Returns:
            Path to temporary directory
        """
        return self.temp_dir

    def get_pipeline_id(self) -> str:
        """Get the pipeline ID.

        Returns:
            Pipeline ID string
        """
        return self.pipeline_id

    def get_config(self) -> PipelineConfig:
        """Get the pipeline configuration.

        Returns:
            Pipeline configuration
        """
        return self.config
