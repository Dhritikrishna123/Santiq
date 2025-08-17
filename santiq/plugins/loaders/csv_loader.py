"""CSV loader plugin for Santiq.

This plugin writes data to CSV files with configurable options including
separators, encoding, and formatting. It supports incremental loading
via append mode and provides comprehensive error handling.
"""

from pathlib import Path
from typing import Any, Dict, List

import pandas as pd

from santiq.plugins.base.loader import LoaderPlugin, LoadResult


class CSVLoader(LoaderPlugin):
    """CSV loader plugin for Santiq.

    Loads data to CSV files with comprehensive configuration options.
    Supports all standard pandas to_csv parameters and provides robust
    error handling for file operations.

    Configuration Parameters:
        path (str): Output file path (required)
        sep (str): Field separator (default: ',')
        encoding (str): File encoding (default: 'utf-8')
        index (bool): Whether to write row indices (default: False)
        header (bool): Whether to write column names (default: True)
        mode (str): Write mode ('w' for overwrite, 'a' for append)
        na_rep (str): String representation for NaN values
        float_format (str): Format string for floating point numbers

    Example Configuration:
        {
            "path": "/path/to/output.csv",
            "sep": ";",
            "encoding": "utf-8",
            "index": False,
            "mode": "w"
        }
    """

    __plugin_name__ = "CSV Loader"
    __version__ = "0.1.0"
    __description__ = "Load data to CSV files with configurable options"
    __api_version__ = "1.0"

    def _validate_config(self) -> None:
        """Validate CSV loader configuration.

        Ensures that the required 'path' parameter is provided and
        validates that the output directory can be created.

        Raises:
            ValueError: If required configuration is missing
        """
        if "path" not in self.config:
            raise ValueError("CSV loader requires 'path' parameter")

    def load(self, data: pd.DataFrame) -> LoadResult:
        """Load data into CSV file.

        Writes the input DataFrame to a CSV file with the configured
        parameters. Creates output directories if they don't exist
        and handles various error conditions gracefully.

        Args:
            data: DataFrame to write to CSV

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

        # Extract pandas to_csv parameters
        pandas_params = {
            k: v
            for k, v in self.config.items()
            if k not in ["path"] and k in self._get_valid_pandas_params()
        }

        # Set sensible defaults for common parameters
        pandas_params.setdefault("index", False)
        pandas_params.setdefault("encoding", "utf-8")

        try:
            data.to_csv(path, **pandas_params)

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
                    "encoding": pandas_params.get("encoding", "utf-8"),
                    "separator": pandas_params.get("sep", ","),
                },
            )
        except Exception as e:
            return LoadResult(
                success=False,
                rows_loaded=0,
                metadata={"error": str(e), "output_path": path},
            )

    def _get_valid_pandas_params(self) -> List[str]:
        """Get list of valid pandas to_csv parameters.

        Returns:
            List of parameter names that can be passed to pandas to_csv
        """
        return [
            "sep",
            "na_rep",
            "float_format",
            "columns",
            "header",
            "index",
            "index_label",
            "mode",
            "encoding",
            "compression",
            "quoting",
            "quotechar",
            "line_terminator",
            "chunksize",
            "date_format",
            "doublequote",
            "escapechar",
            "decimal",
        ]

    def supports_incremental(self) -> bool:
        """Check if this loader supports incremental loading.

        CSV loader supports incremental loading via append mode
        when the 'mode' parameter is set to 'a'.

        Returns:
            True if append mode is configured, False otherwise
        """
        return self.config.get("mode") == "a"
