"""JSON loader plugin for Santiq.

This plugin writes data to JSON files with configurable options including
JSON orientation, formatting, and compression. It supports various output
formats and provides comprehensive error handling.
"""

from pathlib import Path
from typing import Any, Dict, List

import pandas as pd

from santiq.plugins.base.loader import LoaderPlugin, LoadResult


class JSONLoader(LoaderPlugin):
    """JSON loader plugin for Santiq.

    Loads data to JSON files with comprehensive configuration options.
    Supports all standard pandas to_json parameters and provides robust
    error handling for file operations.

    Configuration Parameters:
        path (str): Output file path (required)
        orient (str): JSON orientation ('records', 'split', 'index', 'columns', 'values', 'table')
        index (bool): Whether to write row indices (default: False)
        indent (int): Number of spaces for indentation (default: None)
        date_format (str): Date format string ('epoch', 'iso')
        double_precision (int): Number of decimal places for floats
        force_ascii (bool): Whether to force ASCII encoding (default: True)
        compression (str): Compression type ('gzip', 'bz2', 'zip', 'xz')

    Example Configuration:
        {
            "path": "/path/to/output.json",
            "orient": "records",
            "index": false,
            "indent": 2
        }
    """

    __plugin_name__ = "JSON Loader"
    __version__ = "0.1.5"
    __description__ = "Load data to JSON files with configurable options"
    __api_version__ = "1.0"

    def _validate_config(self) -> None:
        """Validate JSON loader configuration.

        Ensures that the required 'path' parameter is provided and
        validates the JSON orientation parameter.

        Raises:
            ValueError: If required configuration is missing or invalid
        """
        if "path" not in self.config:
            raise ValueError("JSON loader requires 'path' parameter")

        # Validate orient parameter if provided
        orient = self.config.get("orient")
        if orient and orient not in [
            "records",
            "split",
            "index",
            "columns",
            "values",
            "table",
        ]:
            raise ValueError(
                f"Invalid 'orient' parameter: {orient}. "
                "Must be one of: records, split, index, columns, values, table"
            )

    def load(self, data: pd.DataFrame) -> LoadResult:
        """Load data into JSON file.

        Writes the input DataFrame to a JSON file with the configured
        parameters. Creates output directories if they don't exist
        and handles various error conditions gracefully.

        Args:
            data: DataFrame to write to JSON

        Returns:
            LoadResult indicating success/failure and metadata
        """
        path = self.config["path"]

        # Create directory if it doesn't exist
        try:
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        except (OSError, PermissionError) as e:
            return LoadResult(
                success=False,
                rows_loaded=0,
                metadata={
                    "error": f"Cannot create directory: {e}",
                    "output_path": path,
                },
            )

        # Extract pandas to_json parameters
        pandas_params = {
            k: v
            for k, v in self.config.items()
            if k not in ["path"] and k in self._get_valid_pandas_params()
        }

        # Set sensible defaults for common parameters
        pandas_params.setdefault("orient", "records")  # Most common format
        pandas_params.setdefault("force_ascii", True)

        # Only set index=False for orientations that support it
        if pandas_params.get("orient") in ["records", "split", "table", "values"]:
            pandas_params.setdefault("index", False)

        try:
            data.to_json(path, **pandas_params)

            # Verify file was created and get metadata
            file_path = Path(path)
            file_size = file_path.stat().st_size if file_path.exists() else 0

            return LoadResult(
                success=True,
                rows_loaded=len(data),
                metadata={
                    "output_path": path,
                    "columns": list(data.columns),
                    "file_size_bytes": file_size,
                    "json_format": pandas_params.get("orient", "records"),
                    "indent": pandas_params.get("indent"),
                    "compression": pandas_params.get("compression"),
                },
            )
        except Exception as e:
            return LoadResult(
                success=False,
                rows_loaded=0,
                metadata={"error": str(e), "output_path": path},
            )

    def _get_valid_pandas_params(self) -> List[str]:
        """Get list of valid pandas to_json parameters.

        Returns:
            List of parameter names that can be passed to pandas to_json
        """
        return [
            "orient",
            "date_format",
            "double_precision",
            "force_ascii",
            "date_unit",
            "default_handler",
            "lines",
            "compression",
            "index",
            "indent",
            "storage_options",
        ]

    def supports_incremental(self) -> bool:
        """Check if this loader supports incremental loading.

        JSON loader supports incremental loading via JSON lines format
        when the 'lines' parameter is set to True.

        Returns:
            True if JSON lines format is configured, False otherwise
        """
        return self.config.get("lines") is True
