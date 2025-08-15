# Plugin Development Guide

This guide walks you through creating plugins for the Santiq platform.

## Plugin Types

Santiq supports four types of plugins:

1. **Extractors**: Bring data into the pipeline
2. **Profilers**: Analyze data quality and detect issues
3. **Transformers**: Clean, transform, and fix data
4. **Loaders**: Output data to destinations

## Creating Your First Plugin

### 1. Plugin Structure

Each plugin must inherit from the appropriate base class and implement required methods:

```python
from santiq.plugins.base.extractor import ExtractorPlugin
import pandas as pd

class MyExtractor(ExtractorPlugin):
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

### 2. Plugin Manifest (plugin.yml)

For local development, create a `plugin.yml` file:

```yaml
name: "my_custom_extractor"
type: "extractor"
version: "1.0.0"
api_version: "1.0"
description: "Extracts data from my custom source"
entry_point: "my_extractor:MyExtractor"
```

### 3. Package Setup (for distribution)

Create a `pyproject.toml` file:

```toml
[project]
name = "santiq-plugin-mycustom"
version = "1.0.0"
dependencies = ["santiq>=0.1.0"]

[project.entry-points."santiq.extractors"]
my_custom_extractor = "my_extractor:MyExtractor"
```

## Plugin API Reference

### Base Classes

#### ExtractorPlugin

```python
class ExtractorPlugin(ABC):
    def setup(self, config: dict) -> None: ...
    def teardown(self) -> None: ...
    def extract(self) -> pd.DataFrame: ...  # Required
    def get_schema_info(self) -> dict: ...
```

#### ProfilerPlugin

```python
class ProfilerPlugin(ABC):
    def setup(self, config: dict) -> None: ...
    def teardown(self) -> None: ...
    def profile(self, data: pd.DataFrame) -> ProfileResult: ...  # Required
```

#### TransformerPlugin

```python
class TransformerPlugin(ABC):
    def setup(self, config: dict) -> None: ...
    def teardown(self) -> None: ...
    def transform(self, data: pd.DataFrame) -> TransformResult: ...  # Required
    def can_handle_issue(self, issue_type: str) -> bool: ...
    def suggest_fixes(self, data: pd.DataFrame, issues: list) -> list: ...
```

#### LoaderPlugin

```python
class LoaderPlugin(ABC):
    def setup(self, config: dict) -> None: ...
    def teardown(self) -> None: ...
    def load(self, data: pd.DataFrame) -> LoadResult: ...  # Required
    def supports_incremental(self) -> bool: ...
```

## Advanced Features

### Error Handling

Plugins should handle errors gracefully:

```python
def extract(self) -> pd.DataFrame:
    try:
        return self._do_extraction()
    except ConnectionError as e:
        raise Exception(f"Failed to connect to data source: {e}")
    except Exception as e:
        raise Exception(f"Extraction failed: {e}")
```

### Configuration Validation

Always validate your plugin configuration:

```python
def _validate_config(self) -> None:
    required_params = ["host", "database", "table"]
    for param in required_params:
        if param not in self.config:
            raise ValueError(f"Missing required parameter: {param}")
    
    if not isinstance(self.config["port"], int):
        raise ValueError("Port must be an integer")
```

### Memory Management

For large datasets, consider streaming or chunking:

```python
def extract(self) -> pd.DataFrame:
    if self.config.get("use_chunks", False):
        chunks = []
        for chunk in self._extract_chunks():
            chunks.append(chunk)
        return pd.concat(chunks, ignore_index=True)
    else:
        return self._extract_all()
```

## Testing Your Plugin

Create comprehensive tests:

```python
import pytest
from my_plugin import MyExtractor

def test_my_extractor():
    extractor = MyExtractor()
    extractor.setup({"connection_string": "test://localhost"})
    
    result = extractor.extract()
    
    assert isinstance(result, pd.DataFrame)
    assert len(result) > 0
    assert "expected_column" in result.columns
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

### 3. Adding to Official Registry

Submit a PR to add your plugin to the official plugin registry at `registry/plugins.yml`.

## Best Practices

1. **Keep plugins focused**: Each plugin should do one thing well
2. **Validate inputs**: Always validate configuration and data inputs
3. **Handle errors gracefully**: Provide helpful error messages
4. **Document thoroughly**: Include docstrings and type hints
5. **Test comprehensively**: Cover happy path and edge cases
6. **Follow conventions**: Use the established naming and structure patterns
7. **Optimize for performance**: Consider memory usage and processing time
8. **Support configuration**: Make your plugin configurable for different use cases

## Community

- Submit issues and feature requests on GitHub
- Join our Discord for plugin development discussions
- Contribute to the plugin registry
- Share your plugins with the community

Happy plugin development! 🚀
