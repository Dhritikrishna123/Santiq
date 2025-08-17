"""CSV extractor plugin for Santiq.

This plugin extracts data from CSV files using pandas, with support for
various pandas read_csv parameters and comprehensive error handling.
"""

from typing import Any, Dict, List, Optional

import pandas as pd

from santiq.plugins.base.extractor import ExtractorPlugin


class CSVExtractor(ExtractorPlugin):
    """CSV extractor plugin for Santiq.

    Extracts data from CSV files with configurable options including
    separators, encoding, data types, and more. Supports all standard
    pandas read_csv parameters for maximum flexibility.

    Configuration Parameters:
        path (str): Path to the CSV file (required)
        sep (str): Field separator (default: ',')
        encoding (str): File encoding (default: 'utf-8')
        header (int): Row number to use as column names
        dtype (dict): Data types for specific columns
        na_values (list): Values to treat as NaN
        skiprows (int): Number of rows to skip
        nrows (int): Number of rows to read

    Example Configuration:
        {
            "path": "/path/to/data.csv",
            "sep": ";",
            "encoding": "latin-1",
            "header": 0,
            "dtype": {"id": "int64", "price": "float64"}
        }
    """

    __plugin_name__ = "CSV Extractor"
    __version__ = "0.1.0"
    __description__ = "Extracts data from CSV files with configurable options"
    __api_version__ = "1.0"

    def _validate_config(self) -> None:
        """Validate the configuration for the CSV extractor.

        Ensures that the required 'path' parameter is provided.

        Raises:
            ValueError: If required configuration is missing
        """
        if "path" not in self.config:
            raise ValueError("CSV Extractor requires 'path' parameter")

    def extract(self) -> pd.DataFrame:
        """Extract data from CSV file.

        Reads the CSV file using pandas with the configured parameters
        and returns the data as a pandas DataFrame.

        Returns:
            DataFrame containing the extracted data

        Raises:
            Exception: If CSV reading fails (with detailed error message)
        """
        path = self.config.get("path")
        if not path:
            raise Exception("CSV extractor requires 'path' parameter in configuration")

        # Validate that the file exists and is readable
        import os

        if not os.path.exists(str(path)):
            raise Exception(f"Failed to read CSV file '{path}': File not found")

        if not os.access(str(path), os.R_OK):
            raise Exception(f"Failed to read CSV file '{path}': File not readable")

        # Extract pandas read_csv parameters
        pandas_params = {
            k: v
            for k, v in self.config.items()
            if k not in ["path"] and k in self._get_valid_pandas_params()
        }

        # Set sensible defaults for common parameters
        pandas_params.setdefault("encoding", "utf-8")
        pandas_params.setdefault("low_memory", False)  # Better for large files

        try:
            data = pd.read_csv(str(path), **pandas_params)
            return data
        except UnicodeDecodeError as e:
            # Provide helpful error message for encoding issues
            raise Exception(
                f"Encoding error reading CSV file '{path}'. "
                f"Try setting 'encoding' parameter (e.g., 'latin-1', 'cp1252'): {e}"
            )
        except pd.errors.EmptyDataError:
            raise Exception(f"CSV file '{path}' is empty or contains no data")
        except pd.errors.ParserError as e:
            raise Exception(
                f"CSV parsing error in file '{path}'. "
                f"Check file format and separator settings: {e}"
            )
        except Exception as e:
            raise Exception(f"Failed to read CSV file '{path}': {e}")

    def _get_valid_pandas_params(self) -> List[str]:
        """Get list of valid pandas read_csv parameters.

        Returns:
            List of parameter names that can be passed to pandas read_csv
        """
        return [
            "sep",
            "delimiter",
            "header",
            "names",
            "index_col",
            "usecols",
            "dtype",
            "engine",
            "converters",
            "true_values",
            "false_values",
            "skipinitialspace",
            "skiprows",
            "skipfooter",
            "nrows",
            "na_values",
            "keep_default_na",
            "na_filter",
            "skip_blank_lines",
            "parse_dates",
            "date_parser",
            "dayfirst",
            "cache_dates",
            "encoding",
            "compression",
            "thousands",
            "decimal",
            "comment",
            "lineterminator",
            "quotechar",
            "quoting",
            "doublequote",
            "escapechar",
            "low_memory",
            "memory_map",
        ]

    def get_schema_info(self) -> Dict[str, Any]:
        """Get schema information of the CSV file.

        Reads a sample of the CSV file to determine column names,
        data types, and provide metadata about the data structure.

        Returns:
            Dictionary containing schema information:
                - columns: List of column names
                - data_types: Dictionary mapping columns to data types
                - estimated_rows: Estimated number of rows (None if cannot determine)
        """
        try:
            path = self.config.get("path")
            if not path:
                raise Exception(
                    "CSV extractor requires 'path' parameter in configuration"
                )

            # Read first few rows to get schema info
            sample = pd.read_csv(str(path), nrows=5)

            # Try to get row count for small files
            estimated_rows = None
            try:
                # Count lines in file (rough estimate)
                import os

                with open(str(path), "r", encoding="utf-8") as f:
                    line_count = sum(1 for _ in f)
                # Subtract header if present
                header_rows = 1 if self.config.get("header", 0) is not None else 0
                estimated_rows = max(0, line_count - header_rows)
            except:
                pass  # Don't fail if we can't count lines

            return {
                "columns": sample.columns.tolist(),
                "data_types": {col: str(dtype) for col, dtype in sample.dtypes.items()},
                "estimated_rows": estimated_rows,
            }

        except Exception as e:
            # Return minimal info if schema detection fails
            return {
                "columns": [],
                "data_types": {},
                "estimated_rows": None,
                "error": f"Failed to detect schema: {str(e)}",
            }
