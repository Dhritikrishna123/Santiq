# Plugin Development Guide for Santiq

This guide walks you through creating plugins for the Santiq ETL platform.

## Overview

Santiq is a lightweight, modular, plugin-first ETL platform that supports four types of plugins:

1. **Extractors**: Bring data into the pipeline from various sources
2. **Profilers**: Analyze data quality and detect issues
3. **Transformers**: Clean, transform, and fix data
4. **Loaders**: Output data to various destinations

## Plugin Architecture

All plugins inherit from base classes in `santiq.plugins.base.*` and must implement specific interfaces. Plugins are discovered through Python entry points and can be distributed as separate packages.

## Creating Your First Plugin

### 1. Plugin Structure

Each plugin must inherit from the appropriate base class and implement required methods:

```python
from santiq.plugins.base.extractor import ExtractorPlugin
import pandas as pd

class MyCustomExtractor(ExtractorPlugin):
    __plugin_name__ = "My Custom Extractor"
    __api_version__ = "1.0"
    __description__ = "Extracts data from my custom source"
    
    def _validate_config(self):
        if "connection_string" not in self.config:
            raise ValueError("connection_string is required")
    
    def extract(self) -> pd.DataFrame:
        # Your extraction logic here
        return pd.DataFrame({"col1": [1, 2, 3]})
```

### 2. Plugin Metadata

Every plugin must define these class attributes:

- `__plugin_name__`: Human-readable name for the plugin
- `__api_version__`: API version (currently "1.0")
- `__description__`: Brief description of what the plugin does

### 3. Package Setup (for distribution)

Create a `pyproject.toml` file:

```toml
[project]
name = "santiq-plugin-mycustom"
version = "1.0.0"
description = "My custom plugin for Santiq"
dependencies = ["santiq>=0.1.0", "pandas>=2.0.0"]

[project.entry-points."santiq.extractors"]
my_custom_extractor = "my_plugin:MyCustomExtractor"
```

## Plugin Types and Interfaces

### ExtractorPlugin

Extractors bring data into the pipeline from external sources.

```python
from santiq.plugins.base.extractor import ExtractorPlugin
import pandas as pd

class MyExtractor(ExtractorPlugin):
    __plugin_name__ = "My Extractor"
    __api_version__ = "1.0"
    __description__ = "Extracts data from my source"
    
    def _validate_config(self) -> None:
        """Validate plugin configuration."""
        if "source_path" not in self.config:
            raise ValueError("source_path is required")
    
    def extract(self) -> pd.DataFrame:
        """Extract data and return as pandas DataFrame."""
        # Implementation here
        return pd.DataFrame()
    
    def get_schema_info(self) -> Dict[str, Any]:
        """Return information about the data schema."""
        return {
            "columns": [],
            "estimated_rows": None,
            "data_types": {},
        }
```

### ProfilerPlugin

Profilers analyze data quality and detect issues.

```python
from santiq.plugins.base.profiler import ProfilerPlugin, ProfileResult
import pandas as pd

class MyProfiler(ProfilerPlugin):
    __plugin_name__ = "My Profiler"
    __api_version__ = "1.0"
    __description__ = "Profiles data for quality issues"
    
    def _validate_config(self) -> None:
        """Validate plugin configuration."""
        pass
    
    def profile(self, data: pd.DataFrame) -> ProfileResult:
        """Profile the data and return issues and suggestions."""
        issues = []
        summary = {"total_rows": len(data)}
        suggestions = []
        
        # Your profiling logic here
        
        return ProfileResult(issues, summary, suggestions)
```

### TransformerPlugin

Transformers clean and transform data.

```python
from santiq.plugins.base.transformer import TransformerPlugin, TransformResult
import pandas as pd

class MyTransformer(TransformerPlugin):
    __plugin_name__ = "My Transformer"
    __api_version__ = "1.0"
    __description__ = "Transforms data according to rules"
    
    def _validate_config(self) -> None:
        """Validate plugin configuration."""
        pass
    
    def transform(self, data: pd.DataFrame) -> TransformResult:
        """Transform the data and return the result."""
        transformed_data = data.copy()
        applied_fixes = []
        
        # Your transformation logic here
        
        return TransformResult(transformed_data, applied_fixes)
    
    def can_handle_issue(self, issue_type: str) -> bool:
        """Check if this transformer can handle a specific issue type."""
        return issue_type in ["my_issue_type"]
    
    def suggest_fixes(self, data: pd.DataFrame, issues: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Suggest fixes for detected issues."""
        suggestions = []
        # Your suggestion logic here
        return suggestions
```

### LoaderPlugin

Loaders output data to destinations.

```python
from santiq.plugins.base.loader import LoaderPlugin, LoadResult
import pandas as pd

class MyLoader(LoaderPlugin):
    __plugin_name__ = "My Loader"
    __api_version__ = "1.0"
    __description__ = "Loads data to my destination"
    
    def _validate_config(self) -> None:
        """Validate plugin configuration."""
        if "destination_path" not in self.config:
            raise ValueError("destination_path is required")
    
    def load(self, data: pd.DataFrame) -> LoadResult:
        """Load the data to the destination."""
        # Your loading logic here
        
        return LoadResult(
            success=True,
            rows_loaded=len(data),
            metadata={"destination": self.config["destination_path"]}
        )
    
    def supports_incremental(self) -> bool:
        """Check if this loader supports incremental loading."""
        return False
```

## Result Classes

### ProfileResult

```python
class ProfileResult:
    def __init__(
        self,
        issues: List[Dict[str, Any]],
        summary: Dict[str, Any],
        suggestions: List[Dict[str, Any]]
    ) -> None:
        self.issues = issues
        self.summary = summary
        self.suggestions = suggestions
```

### TransformResult

```python
class TransformResult:
    def __init__(
        self,
        data: pd.DataFrame,
        applied_fixes: List[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        self.data = data
        self.applied_fixes = applied_fixes
        self.metadata = metadata or {}
```

### LoadResult

```python
class LoadResult:
    def __init__(
        self,
        success: bool,
        rows_loaded: int,
        metadata: Dict[str, Any]
    ) -> None:
        self.success = success
        self.rows_loaded = rows_loaded
        self.metadata = metadata
```

## Error Handling

Plugins should handle errors gracefully and provide meaningful error messages:

```python
def extract(self) -> pd.DataFrame:
    try:
        return self._do_extraction()
    except ConnectionError as e:
        raise Exception(f"Failed to connect to data source: {e}")
    except Exception as e:
        raise Exception(f"Extraction failed: {e}")
```

## Configuration Validation

Always validate your plugin configuration:

```python
def _validate_config(self) -> None:
    required_params = ["host", "database", "table"]
    for param in required_params:
        if param not in self.config:
            raise ValueError(f"Missing required parameter: {param}")
    
    if not isinstance(self.config.get("port", 0), int):
        raise ValueError("Port must be an integer")
```

## Testing Your Plugin

Create comprehensive tests:

```python
import pytest
import pandas as pd
from my_plugin import MyExtractor

def test_my_extractor():
    extractor = MyExtractor()
    extractor.setup({"connection_string": "test://localhost"})
    
    result = extractor.extract()
    
    assert isinstance(result, pd.DataFrame)
    assert len(result) > 0
    assert "expected_column" in result.columns

def test_my_extractor_missing_config():
    extractor = MyExtractor()
    
    with pytest.raises(ValueError, match="connection_string is required"):
        extractor.setup({})
```

## Publishing Your Plugin

### 1. Local Testing

```bash
# Test with local plugin directory
santiq plugin list --local-dir ./my-plugin
santiq run pipeline my-pipeline.yml --plugin-dir ./my-plugin
```

### 2. Publishing to PyPI

```bash
pip install build twine
python -m build
twine upload dist/*
```

### 3. Installing Your Plugin

```bash
santiq plugin install santiq-plugin-mycustom
```

## Best Practices

1. **Keep plugins focused**: Each plugin should do one thing well
2. **Validate inputs**: Always validate configuration and data inputs
3. **Handle errors gracefully**: Provide helpful error messages
4. **Document thoroughly**: Include docstrings and type hints
5. **Test comprehensively**: Cover happy path and edge cases
6. **Follow conventions**: Use the established naming and structure patterns
7. **Optimize for performance**: Consider memory usage and processing time
8. **Support configuration**: Make your plugin configurable for different use cases

## Example: Complete Plugin

Here's a complete example of a CSV extractor plugin:

```python
"""CSV extractor plugin for Santiq."""

from typing import Any, Dict, List
import pandas as pd
from santiq.plugins.base.extractor import ExtractorPlugin

class CSVExtractor(ExtractorPlugin):
    """Extracts data from CSV files."""
    
    __plugin_name__ = "CSV Extractor"
    __api_version__ = "1.0"
    __description__ = "Extracts data from CSV files with configurable options"
    
    def _validate_config(self) -> None:
        """Validate the configuration for the CSV extractor."""
        if 'path' not in self.config:
            raise ValueError("CSV Extractor requires 'path' parameter")
    
    def extract(self) -> pd.DataFrame:
        """Extract data from CSV file."""
        path = self.config.get('path')
        
        # Extract pandas read_csv parameters
        pandas_params = {
            k: v for k, v in self.config.items() 
            if k not in ['path'] and k in self._get_valid_pandas_params()
        }
        
        try:
            data = pd.read_csv(path, **pandas_params)
            return data
        except Exception as e:
            raise Exception(f"Failed to read CSV file '{path}': '{e}'")
    
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
        """Get schema information of the CSV file."""
        try:
            # Read first few rows to get schema info
            sample = pd.read_csv(self.config['path'], nrows=5)
            return {
                "columns": sample.columns.tolist(),
                "data_types": {col: str(dtype) for col, dtype in sample.dtypes.items()},
                "estimated_rows": None  # Would need to count lines for exact number
            }
        except Exception:
            return {"columns": [], "data_types": {}, "estimated_rows": None}
```

## Community

- Submit issues and feature requests on GitHub
- Join our Discord for plugin development discussions
- Contribute to the plugin registry
- Share your plugins with the community

Happy plugin development! 🚀
