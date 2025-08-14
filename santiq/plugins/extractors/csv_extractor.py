"""CSV extractor plugin"""

from typing import Any , Dict , List , Optional

import pandas as pd

from santiq.plugins.base.extractor import ExtractorPlugin


class CSVExtractor(ExtractorPlugin):
    """CSV extractor plugin for SANTIQ."""
    __plugin_name__ = "CSV Extractor"
    __version__ = "0.1.0"
    __description__ = "Extracts data from CSV files with configurable options"
    __api_version__ = "1.0"
    
    def _validate_config(self)-> None:
        """Validate the configuration for the CSV extractor."""
        if 'path' not in self.config:
            raise ValueError("CSV Extractor requires 'path' parameter")
        
    def extract(self) -> pd.DataFrame:
        """Extract data from CSV file."""
        path = self.config.get('path')
        
        # Extract pandas and read_csv parameters
        pandas_params = {
            k:v for k, v in self.config.items() 
            if k not in ['path'] and k in self._get_valid_pandas_params()
        }
        
        try:
            data = pd.read_csv(path, **pandas_params)
            return data
        except Exception as e:  
            raise Exception(f"Failed to read csv file '{path}': '{e}'")
        
        
    def _get_valid_pandas_params(self) -> List[str]:
        """Get list of valid pandas read_csv parameters."""
        return [
            "sep", "delimiter", "header", "names", "index_col", "usecols",
            "dtype", "engine", "converters", "true_values", "false_values",
            "skipinitialspace", "skiprows", "skipfooter", "nrows",
            "na_values", "keep_default_na", "na_filter", "skip_blank_lines",
            "parse_dates", "date_parser", "dayfirst", "cache_dates",
            "encoding", "compression", "thousands", "decimal", "comment",
            "lineterminator", "quotechar", "quoting", "doublequote",
            "escapechar", "low_memory", "memory_map"
        ]
        
    def get_schema_info(self) -> Dict[str, Any]:
        """Get schema information of the csv file"""
        try:
            # Read first few rows to get schema info
            sample = pd.read_csv(self.config['path'], nrows=5)
            return{
                "columns": sample.columns.tolist(),
                "data_types": {col: str(dtype) for col, dtype in sample.dtypes.items()},
                "estimated_rows": None  # Would need to count lines for exact number
            }
            
        except Exception:
            return {"columns": [], "data_types": {}, "estimated_rows": None}