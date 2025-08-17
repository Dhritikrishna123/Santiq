"""Base transformer plugin interface."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

import pandas as pd


class TransformResult:
    """Represents the result of a transformation."""

    def __init__(
        self,
        data: pd.DataFrame,
        applied_fixes: List[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.data = data
        self.applied_fixes = applied_fixes
        self.metadata = metadata or {}


class TransformerPlugin(ABC):
    """Base class for all transformer plugins."""

    __plugin_name__: str = "Base Transformer"
    __plugin_type__: str = "transformer"
    __api_version__: str = "1.0"
    __description__: str = "Base transformer plugin"

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
    def transform(self, data: pd.DataFrame) -> TransformResult:
        """Transform the data and return the result."""
        pass

    def can_handle_issue(self, issue_type: str) -> bool:
        """Check if this transformer can handle a specific issue type."""
        return False

    def suggest_fixes(
        self, data: pd.DataFrame, issues: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Suggest fixes for detected issues."""
        return []
