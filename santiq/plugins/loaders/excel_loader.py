"""Excel loader plugin for Santiq.

This plugin writes data to Excel files with configurable options including
multiple sheets, formatting, and various Excel formats. It supports all
standard pandas to_excel parameters and provides comprehensive error handling.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from santiq.plugins.base.loader import LoaderPlugin, LoadResult


class ExcelLoader(LoaderPlugin):
    """Excel loader plugin for Santiq.

    Loads data to Excel files with comprehensive configuration options.
    Supports multiple sheets, formatting, and various Excel formats.
    Provides robust error handling for file operations.

    __plugin_name__ = "Excel Loader"
    __version__ = "0.1.5"
    __description__ = "Loads data to Excel files with configurable options"
    __api_version__ = "1.0"

    Configuration Parameters:
        path (str): Output file path (required)
        sheet_name (str): Sheet name (default: 'Sheet1')
        engine (str): Excel engine ('openpyxl', 'xlsxwriter') (default: 'openpyxl')
        index (bool): Whether to write row indices (default: False)
        header (bool): Whether to write column headers (default: True)
        startrow (int): Upper left cell row to dump data frame (default: 0)
        startcol (int): Upper left cell column to dump data frame (default: 0)
        freeze_panes (tuple): Freeze panes position (default: None)
        na_rep (str): String representation of NaN (default: '')
        float_format (str): Format string for floating point numbers (default: None)
        columns (list): Columns to write (default: None)
        header_style (dict): Style for header row (default: None)
        index_label (str): Column label for index column (default: None)
        merge_cells (bool): Write MultiIndex and Hierarchical Rows as merged cells (default: True)
        inf_rep (str): String representation of infinity (default: 'inf')
        encoding (str): File encoding (default: 'utf-8')
        mode (str): File mode ('w', 'a') (default: 'w')
        if_sheet_exists (str): How to behave if sheet exists ('error', 'new', 'replace', 'overlay') (default: 'error')
        storage_options (dict): Storage options for cloud storage (default: None)

    Example Configuration:
        {
            "path": "/path/to/output.xlsx",
            "sheet_name": "Data",
            "engine": "openpyxl",
            "index": false,
            "header": true
        }
    """

    def __init__(self) -> None:
        """Initialize the Excel loader."""
        super().__init__()
        self.path: Optional[str] = None
        self.pandas_params: Dict[str, Any] = {}

    def setup(self, config: Dict[str, Any]) -> None:
        """Set up the loader with configuration.

        Args:
            config: Configuration dictionary containing loading parameters
        """
        if "path" not in config:
            raise ValueError("'path' is required in Excel loader configuration")

        self.path = config["path"]

        # Extract pandas-specific parameters
        pandas_param_names = [
            "sheet_name",
            "engine",
            "index",
            "header",
            "startrow",
            "startcol",
            "freeze_panes",
            "na_rep",
            "float_format",
            "columns",
            "header_style",
            "index_label",
            "merge_cells",
            "inf_rep",
            "encoding",
            "mode",
            "if_sheet_exists",
            "storage_options",
        ]

        self.pandas_params = {
            key: config[key] for key in pandas_param_names if key in config
        }

        # Set sensible defaults
        self.pandas_params.setdefault("sheet_name", "Sheet1")
        self.pandas_params.setdefault("engine", "openpyxl")
        self.pandas_params.setdefault("index", False)
        self.pandas_params.setdefault("header", True)

    def load(self, data: pd.DataFrame) -> LoadResult:
        """Load data to Excel file.

        Args:
            data: DataFrame to load

        Returns:
            LoadResult containing operation status and metadata
        """
        try:
            # Ensure output directory exists
            output_path = Path(self.path)  # type: ignore
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Write to Excel
            data.to_excel(self.path, **self.pandas_params)

            # Get file size
            file_size = output_path.stat().st_size if output_path.exists() else 0

            return LoadResult(
                success=True,
                rows_loaded=len(data),
                metadata={
                    "output_path": self.path,
                    "columns": list(data.columns),
                    "file_size_bytes": file_size,
                    "sheet_name": self.pandas_params.get("sheet_name", "Sheet1"),
                    "engine": self.pandas_params.get("engine", "openpyxl"),
                    "index_included": self.pandas_params.get("index", False),
                    "header_included": self.pandas_params.get("header", True),
                    "start_row": self.pandas_params.get("startrow", 0),
                    "start_col": self.pandas_params.get("startcol", 0),
                },
            )

        except Exception as e:
            return LoadResult(
                success=False,
                rows_loaded=0,
                metadata={
                    "error": str(e),
                    "output_path": self.path,
                },
            )

    def load_incremental(self, data: pd.DataFrame, **kwargs: Any) -> LoadResult:
        """Load data incrementally to Excel file.

        Args:
            data: DataFrame to load
            **kwargs: Additional parameters for incremental loading

        Returns:
            LoadResult containing operation status and metadata
        """
        try:
            # For incremental loading, we'll use ExcelWriter to append to existing file
            if_sheet_exists = kwargs.get("if_sheet_exists", "overlay")

            # Update pandas params for incremental mode
            incremental_params = self.pandas_params.copy()
            # Remove if_sheet_exists as it's not a valid parameter for to_excel()
            incremental_params.pop("if_sheet_exists", None)

            # Ensure output directory exists
            output_path = Path(self.path)  # type: ignore
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Use ExcelWriter for incremental loading
            with pd.ExcelWriter(
                self.path,  # type: ignore
                engine=incremental_params.get("engine", "openpyxl"),
                mode="a",
                if_sheet_exists=if_sheet_exists,
            ) as writer:
                data.to_excel(writer, **incremental_params)

            # Get file size
            file_size = output_path.stat().st_size if output_path.exists() else 0

            # Force cleanup of any remaining file handles
            import gc

            gc.collect()

            return LoadResult(
                success=True,
                rows_loaded=len(data),
                metadata={
                    "output_path": self.path,
                    "columns": list(data.columns),
                    "file_size_bytes": file_size,
                    "mode": "a",
                    "if_sheet_exists": if_sheet_exists,
                    "sheet_name": incremental_params.get("sheet_name", "Sheet1"),
                },
            )

        except Exception as e:
            return LoadResult(
                success=False,
                rows_loaded=0,
                metadata={
                    "error": str(e),
                    "output_path": self.path,
                },
            )
