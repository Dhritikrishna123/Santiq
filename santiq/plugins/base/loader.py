"""Base loader plugin interface."""

from abc import ABC, abstractmethod
from typing import Any, Dict

import pandas as pd


class LoadResult:
    """Represents the result of a load operation."""

    def __init__(
        self, success: bool, rows_loaded: int, metadata: Dict[str, Any]
    ) -> None:
        self.success = success
        self.rows_loaded = rows_loaded
        self.metadata = metadata


class LoaderPlugin(ABC):
    """Base class for all loader plugins."""

    __plugin_name__: str = "Base Loader"
    __plugin_type__: str = "loader"
    __api_version__: str = "1.0"
    __description__: str = "Base loader plugin"

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
    def load(self, data: pd.DataFrame) -> LoadResult:
        """Load the data to the destination."""
        pass

    def supports_incremental(self) -> bool:
        """Check if this loader supports incremental loading."""
        return False
