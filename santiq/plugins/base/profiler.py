"""Base profiler plugin interface."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List

import pandas as pd


class ProfileResult:
    """Represents the result of data profiling."""

    def __init__(
        self,
        issues: List[Dict[str, Any]],
        summary: Dict[str, Any],
        suggestions: List[Dict[str, Any]],
    ) -> None:
        self.issues = issues
        self.summary = summary
        self.suggestions = suggestions


class ProfilerPlugin(ABC):
    """Base class for all profiler plugins."""

    __plugin_name__: str = "Base Profiler"
    __plugin_type__: str = "profiler"
    __api_version__: str = "1.0"
    __description__: str = "Base profiler plugin"

    def __init__(self) -> None:
        self.config: Dict[str, Any] = {}

    def setup(self, config: Dict[str, Any]) -> None:
        """Setup plugin with configuration."""
        self.config = config
        self._validate_config()

    def teardown(self) -> None:
        """Cleanup plugin resources."""
        pass

    def _validate_config(self) -> None:
        """Validate plugin configuration. Override in subclasses."""
        pass

    @abstractmethod
    def profile(self, data: pd.DataFrame) -> ProfileResult:
        """Profile the data and return issues and suggestions."""
        pass
