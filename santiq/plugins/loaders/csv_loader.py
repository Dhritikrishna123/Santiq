"""CSV loader plugin."""

from pathlib import Path
from typing import Any, Dict, List

import pandas as pd

from santiq.plugins.base.loader import LoaderPlugin, LoadResult


class CSVLoader(LoaderPlugin):
    """Load Data to CSV files"""
    __plugin_name__ = "CSV Loader"
    __version__ = "0.1.0"
    __description__ = "Load data to CSV files with configurable options"
    __api_version__ = "1.0"
    
    def _validate_config(self):
        """Validate CSV loader configuration"""
        if "path" not in self.config:
            raise ValueError("CSV loader requires 'path' parameter")
        
    def load(self, data: pd.DataFrame) -> LoadResult:
        """Load data into CSV File"""
        path = self.config["path"]
        
        # create directory if doesn't exist
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        
        # Extract pandas to CSV Paramaters 
        pandas_params = {
            k: v for k, v in self.config.items()
            if k not in ["path"] and k in self._get_valid_pandas_params()
        }
        
        # set some sensible defaults 
        pandas_params.setdefault("index", False)
        
        try: 
            data.to_csv(path, **pandas_params)
            
            return LoadResult(
                success=True,
                rows_loaded=len(data),
                metadata={
                    "output_path": path,
                    "columns": list(data.columns),
                    "file_size_bytes": Path(path).stat().st_size if Path(path).exists() else 0
                }
            )
        except Exception as e:
            return LoadResult(
                success=False,
                rows_loaded=0,
                metadata={"error": str(e), "output_path": path}
            )
    
    def _get_valid_pandas_params(self) -> List[str]:
        """Get list of valid pandas to_csv parameters."""
        return [
            "sep", "na_rep", "float_format", "columns", "header", "index",
            "index_label", "mode", "encoding", "compression", "quoting",
            "quotechar", "line_terminator", "chunksize", "date_format",
            "doublequote", "escapechar", "decimal"
        ]
    
    def supports_incremental(self) -> bool:
        """CSV loader supports incremental loading via append mode."""
        return self.config.get("mode") == "a"