"""Excel extractor plugin for Santiq.

This plugin extracts data from Excel files using pandas, with support for
multiple sheets, various Excel formats (xlsx, xls, xlsm, etc.), and
comprehensive error handling.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import pandas as pd

from santiq.plugins.base.extractor import ExtractorPlugin


class ExcelExtractor(ExtractorPlugin):
    """Excel extractor plugin for Santiq.

    Extracts data from Excel files with configurable options including
    sheet selection, header handling, data types, and more. Supports all
    standard pandas read_excel parameters for maximum flexibility.

    __plugin_name__ = "Excel Extractor"
    __version__ = "0.1.5"
    __description__ = "Extracts data from Excel files with configurable options"
    __api_version__ = "1.0"

    Configuration Parameters:
        path (str): Path to the Excel file (required)
        sheet_name (str|int|list): Sheet name, index, or list of sheets (default: 0)
        header (int|list): Row number to use as column labels (default: 0)
        skiprows (int|list): Rows to skip at the beginning (default: None)
        usecols (str|list): Columns to use (default: None)
        engine (str): Excel engine ('openpyxl', 'xlrd', 'odf') (default: 'openpyxl')
        dtype (dict): Data types for columns (default: None)
        na_values (list): Values to treat as NaN (default: None)
        keep_default_na (bool): Whether to keep default NaN values (default: True)
        parse_dates (bool|list): Columns to parse as dates (default: False)
        date_parser (callable): Function to parse dates (default: None)
        thousands (str): Thousands separator (default: None)
        decimal (str): Decimal separator (default: '.')
        comment (str): Character to mark comments (default: None)
        skipfooter (int): Rows to skip at the end (default: 0)
        convert_float (bool): Convert float columns to int if possible (default: True)
        mangle_dupe_cols (bool): Rename duplicate columns (default: True)
        storage_options (dict): Storage options for cloud storage (default: None)

    Example Configuration:
        {
            "path": "/path/to/data.xlsx",
            "sheet_name": "Sheet1",
            "header": 0,
            "skiprows": 2,
            "usecols": "A:C,E:F",
            "engine": "openpyxl"
        }
    """

    def __init__(self) -> None:
        """Initialize the Excel extractor."""
        super().__init__()
        self.path: Optional[str] = None
        self.pandas_params: Dict[str, Any] = {}

    def setup(self, config: Dict[str, Any]) -> None:
        """Set up the extractor with configuration.

        Args:
            config: Configuration dictionary containing extraction parameters
        """
        if "path" not in config:
            raise ValueError("'path' is required in Excel extractor configuration")

        self.path = config["path"]

        # Validate file exists
        if not Path(self.path).exists():
            raise FileNotFoundError(f"Excel file not found: {self.path}")

        # Extract pandas-specific parameters
        pandas_param_names = [
            "sheet_name",
            "header",
            "skiprows",
            "usecols",
            "engine",
            "dtype",
            "na_values",
            "keep_default_na",
            "parse_dates",
            "date_parser",
            "thousands",
            "decimal",
            "comment",
            "skipfooter",
            "convert_float",
            "mangle_dupe_cols",
            "storage_options",
        ]

        self.pandas_params = {
            key: config[key] for key in pandas_param_names if key in config
        }

        # Set sensible defaults
        self.pandas_params.setdefault("sheet_name", 0)
        self.pandas_params.setdefault("header", 0)
        self.pandas_params.setdefault("engine", "openpyxl")

    def extract(self) -> pd.DataFrame:
        """Extract data from Excel file.

        Returns:
            DataFrame containing the extracted data

        Raises:
            Exception: If extraction fails
        """
        try:
            # Read Excel file
            if isinstance(self.pandas_params.get("sheet_name"), list):
                # Multiple sheets - read all and concatenate
                sheets: Any = pd.read_excel(self.path, **self.pandas_params)
                if isinstance(sheets, dict):
                    # Multiple sheets returned as dict
                    dataframes = []
                    for sheet_name, df in sheets.items():
                        df["_sheet_name"] = sheet_name
                        dataframes.append(df)
                    return pd.concat(dataframes, ignore_index=True)
                else:
                    # Single sheet returned
                    return sheets  # type: ignore
            else:
                # Single sheet
                return pd.read_excel(self.path, **self.pandas_params)  # type: ignore

        except Exception as e:
            raise Exception(f"Excel extraction error: {str(e)}")

    def get_schema_info(self) -> Dict[str, Any]:
        """Get schema information about the Excel file.

        Returns:
            Dictionary containing schema information
        """
        try:
            # Read just the first few rows to get schema info
            schema_params = self.pandas_params.copy()
            schema_params["nrows"] = 5  # Read only first 5 rows for schema detection

            df_sample = pd.read_excel(self.path, **schema_params)

            # Get sheet names if multiple sheets
            sheet_names = []
            xl_file = None
            try:
                if isinstance(self.pandas_params.get("sheet_name"), list):
                    sheet_names = self.pandas_params["sheet_name"]
                elif self.pandas_params.get("sheet_name") == 0:
                    # Get all sheet names
                    xl_file = pd.ExcelFile(self.path)  # type: ignore
                    sheet_names = xl_file.sheet_names
                else:
                    sheet_names = [str(self.pandas_params.get("sheet_name", 0))]
            finally:
                # Ensure ExcelFile is properly closed
                if xl_file is not None:
                    xl_file.close()

            return {
                "columns": list(df_sample.columns),
                "data_types": df_sample.dtypes.to_dict(),
                "estimated_rows": len(df_sample),  # This is just a sample
                "sheet_names": sheet_names,
                "file_size_bytes": Path(self.path).stat().st_size,  # type: ignore
                "engine": self.pandas_params.get("engine", "openpyxl"),
                "header_row": self.pandas_params.get("header", 0),
                "skip_rows": self.pandas_params.get("skiprows"),
                "use_columns": self.pandas_params.get("usecols"),
            }
        except Exception as e:
            return {
                "error": f"Schema detection failed: {str(e)}",
                "columns": [],
                "data_types": {},
                "estimated_rows": 0,
                "sheet_names": [],
            }
