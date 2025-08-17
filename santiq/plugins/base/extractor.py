"""Base extractor plugin interface."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

import pandas as pd


class ExtractorPlugin(ABC):
    """Base class for all extractor plugins."""

    __plugin_name__: str = "Base Extractor"
    __plugin_type__: str = "extractor"
    __api_version__: str = "1.0"
    __description__: str = "Base extractor plugin"

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
    def extract(self) -> pd.DataFrame:
        """Extract data and return as pandas DataFrame."""
        pass

    def get_schema_info(self) -> Dict[str, Any]:
        """Return information about the data schema this extractor provides."""
        return {
            "columns": [],
            "estimated_rows": None,
            "data_types": {},
        }
