"""JSON extractor plugin for Santiq.

This plugin extracts data from JSON files using pandas, with support for
various JSON formats (records, split, index, columns, values, table) and
comprehensive error handling.
"""

import json
from typing import Any, Dict, List, Optional

import pandas as pd

from santiq.plugins.base.extractor import ExtractorPlugin


class JSONExtractor(ExtractorPlugin):
    """JSON extractor plugin for Santiq.

    Extracts data from JSON files with configurable options including
    JSON orientation, encoding, data types, and more. Supports all standard
    pandas read_json parameters for maximum flexibility.

    Configuration Parameters:
        path (str): Path to the JSON file (required)
        orient (str): JSON orientation ('records', 'split', 'index', 'columns', 'values', 'table')
        encoding (str): File encoding (default: 'utf-8')
        lines (bool): Whether to read JSON lines format (default: False)
        dtype (dict): Data types for specific columns
        na_values (list): Values to treat as NaN
        nrows (int): Number of rows to read (for lines=True)
        chunksize (int): Number of lines to read per chunk (for lines=True)

    Example Configuration:
        {
            "path": "/path/to/data.json",
            "orient": "records",
            "encoding": "utf-8",
            "lines": false,
            "dtype": {"id": "int64", "price": "float64"}
        }
    """

    __plugin_name__ = "JSON Extractor"
    __version__ = "0.1.0"
    __description__ = "Extracts data from JSON files with configurable options"
    __api_version__ = "1.0"

    def _validate_config(self) -> None:
        """Validate the configuration for the JSON extractor.

        Ensures that the required 'path' parameter is provided and
        validates the JSON orientation parameter.

        Raises:
            ValueError: If required configuration is missing or invalid
        """
        if "path" not in self.config:
            raise ValueError("JSON Extractor requires 'path' parameter")

        # Validate orient parameter if provided
        orient = self.config.get("orient")
        if orient and orient not in ["records", "split", "index", "columns", "values", "table"]:
            raise ValueError(
                f"Invalid 'orient' parameter: {orient}. "
                "Must be one of: records, split, index, columns, values, table"
            )

    def extract(self) -> pd.DataFrame:
        """Extract data from JSON file.

        Reads the JSON file using pandas with the configured parameters
        and returns the data as a pandas DataFrame.

        Returns:
            DataFrame containing the extracted data

        Raises:
            Exception: If JSON reading fails (with detailed error message)
        """
        path = self.config.get("path")
        if not path:
            raise Exception("JSON extractor requires 'path' parameter in configuration")

        # Validate that the file exists and is readable
        import os

        if not os.path.exists(str(path)):
            raise Exception(f"Failed to read JSON file '{path}': File not found")

        if not os.access(str(path), os.R_OK):
            raise Exception(f"Failed to read JSON file '{path}': File not readable")

        # Extract pandas read_json parameters
        pandas_params = {
            k: v
            for k, v in self.config.items()
            if k not in ["path"] and k in self._get_valid_pandas_params()
        }

        # Set sensible defaults for common parameters
        pandas_params.setdefault("encoding", "utf-8")
        pandas_params.setdefault("orient", "records")  # Most common format

        try:
            data = pd.read_json(str(path), **pandas_params)
            return data  # type: ignore[no-any-return]
        except json.JSONDecodeError as e:
            # Provide helpful error message for JSON parsing issues
            raise Exception(
                f"JSON parsing error in file '{path}'. "
                f"Check file format and JSON syntax: {e}"
            )
        except UnicodeDecodeError as e:
            # Provide helpful error message for encoding issues
            raise Exception(
                f"Encoding error reading JSON file '{path}'. "
                f"Try setting 'encoding' parameter (e.g., 'latin-1', 'cp1252'): {e}"
            )
        except pd.errors.EmptyDataError:
            raise Exception(f"JSON file '{path}' is empty or contains no data")
        except Exception as e:
            raise Exception(f"Failed to read JSON file '{path}': {e}")

    def _get_valid_pandas_params(self) -> List[str]:
        """Get list of valid pandas read_json parameters.

        Returns:
            List of parameter names that can be passed to pandas read_json
        """
        return [
            "orient",
            "typ",
            "dtype",
            "convert_axes",
            "convert_dates",
            "keep_default_dates",
            "numpy",
            "precise_float",
            "date_unit",
            "encoding",
            "lines",
            "chunksize",
            "compression",
            "nrows",
            "storage_options",
        ]

    def get_schema_info(self) -> Dict[str, Any]:
        """Get schema information of the JSON file.

        Reads a sample of the JSON file to determine column names,
        data types, and provide metadata about the data structure.

        Returns:
            Dictionary containing schema information:
                - columns: List of column names
                - data_types: Dictionary mapping columns to data types
                - estimated_rows: Estimated number of rows (None if cannot determine)
                - json_format: Detected JSON format (records, split, etc.)
        """
        try:
            path = self.config.get("path")
            if not path:
                raise Exception(
                    "JSON extractor requires 'path' parameter in configuration"
                )

            # Read first few rows to get schema info
            sample_params = self.config.copy()
            sample_params["nrows"] = 5  # Read only 5 rows for schema detection
            
            # Remove path from sample params
            sample_params.pop("path", None)
            
            # Set defaults for schema detection
            sample_params.setdefault("encoding", "utf-8")
            sample_params.setdefault("orient", "records")

            sample = pd.read_json(str(path), **sample_params)

            # Try to get row count for small files
            estimated_rows = None
            json_format = sample_params.get("orient", "records")
            
            try:
                # For JSON lines format, count lines
                if sample_params.get("lines", False):
                    with open(str(path), "r", encoding=sample_params.get("encoding", "utf-8")) as f:
                        line_count = sum(1 for _ in f)
                    estimated_rows = line_count
                else:
                    # For regular JSON, try to parse and count
                    with open(str(path), "r", encoding=sample_params.get("encoding", "utf-8")) as f:
                        json_data = json.load(f)
                    
                    if json_format == "records" and isinstance(json_data, list):
                        estimated_rows = len(json_data)
                    elif json_format == "split" and isinstance(json_data, dict):
                        estimated_rows = len(json_data.get("data", []))
                    elif json_format == "index" and isinstance(json_data, dict):
                        estimated_rows = len(json_data)
                    elif json_format == "columns" and isinstance(json_data, dict):
                        # Count the length of the first column
                        first_col = next(iter(json_data.values()), [])
                        estimated_rows = len(first_col) if isinstance(first_col, list) else None
            except:
                pass  # Don't fail if we can't count rows

            return {
                "columns": sample.columns.tolist(),
                "data_types": {col: str(dtype) for col, dtype in sample.dtypes.items()},
                "estimated_rows": estimated_rows,
                "json_format": json_format,
            }

        except Exception as e:
            # Return minimal info if schema detection fails
            return {
                "columns": [],
                "data_types": {},
                "estimated_rows": None,
                "json_format": "unknown",
                "error": f"Failed to detect schema: {str(e)}",
            }
