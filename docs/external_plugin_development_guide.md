# Santiq External Plugin Development Guide

## Table of Contents
1. [Introduction](#introduction)
2. [Plugin Architecture Overview](#plugin-architecture-overview)
3. [Plugin Types](#plugin-types)
4. [Getting Started](#getting-started)
5. [Plugin Development](#plugin-development)
6. [Testing Your Plugin](#testing-your-plugin)
7. [Packaging and Distribution](#packaging-and-distribution)
8. [External Plugin Management](#external-plugin-management)
9. [Best Practices](#best-practices)
10. [Troubleshooting](#troubleshooting)
11. [Examples](#examples)

## Introduction

Santiq is a powerful ETL (Extract, Transform, Load) framework that supports external plugins. This guide will walk you through the process of developing, testing, and distributing your own plugins for the Santiq ecosystem.

### What are External Plugins?

External plugins allow you to extend Santiq's functionality without modifying the core codebase. They can be:
- **Extractors**: Read data from various sources (databases, APIs, files, etc.)
- **Transformers**: Clean, validate, and transform data
- **Profilers**: Analyze data quality and detect issues
- **Loaders**: Write data to various destinations

### Why Develop External Plugins?

1. **Extensibility**: Add support for new data sources or destinations
2. **Customization**: Implement business-specific data transformations
3. **Reusability**: Share plugins with the community
4. **Maintainability**: Keep custom logic separate from core framework

## Plugin Architecture Overview

Santiq uses a plugin architecture based on Python's entry points system. Plugins are discovered and loaded dynamically at runtime.

### Core Components

1. **Plugin Manager**: Discovers and loads plugins
2. **Base Classes**: Define the interface for each plugin type
3. **Entry Points**: Registration mechanism for plugins
4. **Configuration**: Plugin-specific settings and parameters

### Plugin Discovery

Plugins are discovered through:
- **Entry Points**: Registered in `setup.py` or `pyproject.toml`
- **Local Directories**: For development and testing
- **PyPI**: For distributed plugins

## Plugin Types

### 1. Extractor Plugins

Extractors read data from external sources and return pandas DataFrames.

**Base Class**: `santiq.plugins.base.extractor.ExtractorPlugin`

**Required Methods**:
- `extract()`: Extract data and return DataFrame
- `get_schema_info()`: Return schema information

**Example Use Cases**:
- Database connectors (PostgreSQL, MySQL, etc.)
- API clients (REST, GraphQL, etc.)
- File readers (CSV, JSON, Excel, etc.)

### 2. Transformer Plugins

Transformers clean, validate, and transform data.

**Base Class**: `santiq.plugins.base.transformer.TransformerPlugin`

**Required Methods**:
- `transform(data)`: Transform input DataFrame and return TransformResult

**Example Use Cases**:
- Data cleaning (remove duplicates, handle missing values)
- Data validation (check formats, ranges, etc.)
- Data enrichment (add calculated fields, lookups, etc.)

### 3. Profiler Plugins

Profilers analyze data quality and detect issues.

**Base Class**: `santiq.plugins.base.profiler.ProfilerPlugin`

**Required Methods**:
- `profile(data)`: Analyze data and return ProfileResult

**Example Use Cases**:
- Data quality assessment
- Anomaly detection
- Statistical analysis

### 4. Loader Plugins

Loaders write data to external destinations.

**Base Class**: `santiq.plugins.base.loader.LoaderPlugin`

**Required Methods**:
- `load(data)`: Write DataFrame to destination and return LoadResult

**Example Use Cases**:
- Database writers
- File writers (CSV, JSON, Parquet, etc.)
- API endpoints

## Getting Started

### Prerequisites

1. **Python 3.8+**: Required for plugin development
2. **Santiq**: Install the core framework
3. **Development Tools**: Your preferred IDE and testing framework

### Installation

```bash
# Install Santiq
pip install santiq

# For development
git clone https://github.com/your-org/santiq
cd santiq
pip install -e .
```

### Project Structure

Create a new directory for your plugin:

```
my-santiq-plugin/
├── src/
│   └── my_santiq_plugin/
│       ├── __init__.py
│       ├── extractor.py
│       ├── transformer.py
│       └── loader.py
├── tests/
│   ├── __init__.py
│   ├── test_extractor.py
│   └── test_transformer.py
├── pyproject.toml
├── README.md
└── LICENSE
```

## Plugin Development

### Step 1: Choose Your Plugin Type

Decide what type of plugin you want to create based on your needs:

- **Extractor**: If you need to read from a new data source
- **Transformer**: If you need to clean or transform data
- **Profiler**: If you need to analyze data quality
- **Loader**: If you need to write to a new destination

### Step 2: Create the Plugin Class

Here's a minimal example of an extractor plugin:

```python
import pandas as pd
from santiq.plugins.base.extractor import ExtractorPlugin

class MyCustomExtractor(ExtractorPlugin):
    """My custom data extractor."""
    
    # Required metadata
    __plugin_name__ = "My Custom Extractor"
    __api_version__ = "1.0"
    __description__ = "Extracts data from my custom source"
    __version__ = "1.0.0"
    
    def _validate_config(self) -> None:
        """Validate plugin configuration."""
        if "source_url" not in self.config:
            raise ValueError("source_url parameter is required")
    
    def extract(self) -> pd.DataFrame:
        """Extract data from the configured source."""
        source_url = self.config["source_url"]
        
        # Your custom extraction logic here
        data = self._fetch_data(source_url)
        
        return pd.DataFrame(data)
    
    def get_schema_info(self) -> dict:
        """Return schema information."""
        return {
            "columns": ["id", "name", "value"],
            "data_types": {
                "id": "int64",
                "name": "object",
                "value": "float64"
            },
            "estimated_rows": 1000
        }
    
    def _fetch_data(self, url: str) -> list:
        """Fetch data from the source URL."""
        # Implement your data fetching logic
        # This is just an example
        return [
            {"id": 1, "name": "Item 1", "value": 10.5},
            {"id": 2, "name": "Item 2", "value": 20.3}
        ]
```

### Step 3: Add Required Metadata

Every plugin must have these attributes:

- `__plugin_name__`: Human-readable name
- `__api_version__`: API version (use "1.0" for current version)
- `__description__`: Brief description of what the plugin does
- `__version__`: Plugin version (semantic versioning recommended)

### Step 4: Implement Required Methods

Each plugin type has specific required methods:

#### Extractor Plugins

```python
def extract(self) -> pd.DataFrame:
    """Extract data and return as DataFrame."""
    # Your extraction logic here
    pass

def get_schema_info(self) -> dict:
    """Return schema information."""
    return {
        "columns": ["col1", "col2"],
        "data_types": {"col1": "object", "col2": "int64"},
        "estimated_rows": 1000
    }
```

#### Transformer Plugins

```python
def transform(self, data: pd.DataFrame) -> TransformResult:
    """Transform the input data."""
    transformed_data = data.copy()
    applied_fixes = []
    
    # Your transformation logic here
    
    return TransformResult(transformed_data, applied_fixes, {"meta": "data"})
```

#### Profiler Plugins

```python
def profile(self, data: pd.DataFrame) -> ProfileResult:
    """Profile the input data."""
    issues = []
    summary = {}
    suggestions = []
    
    # Your profiling logic here
    
    return ProfileResult(issues, summary, suggestions)
```

#### Loader Plugins

```python
def load(self, data: pd.DataFrame) -> LoadResult:
    """Load data to destination."""
    # Your loading logic here
    
    return LoadResult(True, len(data), {"destination": "my_dest"})
```

### Step 5: Configuration Validation

Always validate your plugin's configuration:

```python
def _validate_config(self) -> None:
    """Validate plugin configuration."""
    required_params = ["param1", "param2"]
    for param in required_params:
        if param not in self.config:
            raise ValueError(f"Missing required parameter: {param}")
    
    # Validate parameter values
    if self.config.get("timeout", 0) < 0:
        raise ValueError("timeout must be non-negative")
```

## Testing Your Plugin

### Unit Testing

Create comprehensive tests for your plugin:

```python
import pytest
import pandas as pd
from my_santiq_plugin.extractor import MyCustomExtractor

class TestMyCustomExtractor:
    def test_valid_config(self):
        """Test plugin with valid configuration."""
        config = {"source_url": "https://api.example.com/data"}
        extractor = MyCustomExtractor()
        extractor.setup(config)
        
        data = extractor.extract()
        assert isinstance(data, pd.DataFrame)
        assert len(data) > 0
    
    def test_invalid_config(self):
        """Test plugin with invalid configuration."""
        extractor = MyCustomExtractor()
        
        with pytest.raises(ValueError, match="source_url"):
            extractor.setup({})
    
    def test_schema_info(self):
        """Test schema information."""
        extractor = MyCustomExtractor()
        schema = extractor.get_schema_info()
        
        assert "columns" in schema
        assert "data_types" in schema
        assert "estimated_rows" in schema
```

### Integration Testing

Test your plugin with the Santiq framework:

```python
from santiq.core.engine import ETLEngine
from santiq.core.config import PipelineConfig

def test_plugin_integration():
    """Test plugin integration with Santiq."""
    engine = ETLEngine()
    
    config = PipelineConfig(
        extractor={
            'plugin': 'my_custom_extractor',
            'params': {'source_url': 'https://api.example.com/data'}
        },
        transformers=[{
            'plugin': 'basic_cleaner',
            'params': {'drop_nulls': True}
        }],
        loaders=[{
            'plugin': 'csv_loader',
            'params': {'path': '/tmp/output.csv'}
        }]
    )
    
    result = engine.run_pipeline_from_config(config)
    assert result['success'] is True
```

### Local Testing

Test your plugin locally before publishing:

```bash
# Install your plugin in development mode
pip install -e .

# Test with Santiq CLI
santiq plugin list --local-dir /path/to/your/plugin

# Test plugin functionality
santiq plugin info my_custom_extractor
```

## Packaging and Distribution

### Step 1: Configure Entry Points

Add entry points to your `pyproject.toml`:

```toml
[project.entry-points."santiq.extractors"]
my_custom_extractor = "my_santiq_plugin.extractor:MyCustomExtractor"

[project.entry-points."santiq.transformers"]
my_custom_transformer = "my_santiq_plugin.transformer:MyCustomTransformer"

[project.entry-points."santiq.loaders"]
my_custom_loader = "my_santiq_plugin.loader:MyCustomLoader"
```

### Step 2: Package Your Plugin

```bash
# Build the package
python -m build

# Check the package
twine check dist/*
```

### Step 3: Publish to PyPI

```bash
# Upload to PyPI
twine upload dist/*

# Or upload to TestPyPI first
twine upload --repository testpypi dist/*
```

### Step 4: Install and Test

```bash
# Install your published plugin
pip install my-santiq-plugin

# Verify installation
santiq plugin list
```

## External Plugin Management

Santiq provides a comprehensive system for managing external plugins through configuration files and CLI commands. This allows users to easily discover, install, and manage plugins from PyPI without modifying the core framework.

### Configuration Files

External plugins are configured through YAML configuration files. The system automatically looks for these files in the following locations:

1. `~/.santiq/external_plugins.yml` (user configuration)
2. `~/.santiq/external_plugins.yaml` (user configuration)
3. `.santiq/external_plugins.yml` (project configuration)
4. `.santiq/external_plugins.yaml` (project configuration)

#### Configuration Format

```yaml
plugins:
  plugin_name:
    package: "pypi-package-name"
    type: "extractor|transformer|profiler|loader"
    description: "Human-readable description"
    version: "1.0.0"
    api_version: "1.0"
    author: "Plugin Author"
    license: "MIT"
    homepage: "https://github.com/example/plugin"
```

**Required Fields:**
- `package`: The PyPI package name
- `type`: One of extractor, transformer, profiler, or loader

**Optional Fields:**
- `description`: Human-readable description
- `version`: Plugin version
- `api_version`: Santiq API compatibility version
- `author`: Plugin author/developer
- `license`: License information
- `homepage`: URL to plugin homepage or repository

### CLI Commands

Santiq provides a comprehensive set of CLI commands for managing external plugins:

#### List External Plugins

```bash
# List all external plugins
santiq plugin external list

# List external plugins by type
santiq plugin external list --type extractor
```

#### Add External Plugin Configuration

```bash
# Add a new external plugin configuration
santiq plugin external add postgres_extractor \
  --package santiq-plugin-postgres-extractor \
  --type extractor \
  --description "Extract data from PostgreSQL databases" \
  --version "1.0.0" \
  --api-version "1.0"
```

#### Install External Plugin

```bash
# Install an external plugin package
santiq plugin external install postgres_extractor

# Install with custom package name
santiq plugin external install postgres_extractor --package custom-package-name
```

#### Uninstall External Plugin

```bash
# Uninstall an external plugin package
santiq plugin external uninstall postgres_extractor
```

#### Remove External Plugin Configuration

```bash
# Remove external plugin configuration
santiq plugin external remove postgres_extractor
```

### Plugin Discovery

External plugins are automatically discovered by the Santiq framework:

1. **Configuration Loading**: The system loads external plugin configurations from YAML files
2. **Package Verification**: Checks if PyPI packages are installed
3. **Plugin Registration**: Registers installed plugins for use in pipelines
4. **Status Tracking**: Tracks installation status (installed/not installed)

### Using External Plugins in Pipelines

Once configured and installed, external plugins can be used in pipeline configurations just like built-in plugins:

```yaml
# pipeline.yml
extractor:
  plugin: postgres_extractor
  params:
    host: "localhost"
    database: "mydb"
    query: "SELECT * FROM users"

transformers:
  - plugin: json_transformer
    params:
      output_format: "json"
      validate_schema: true

loaders:
  - plugin: elasticsearch_loader
    params:
      host: "localhost:9200"
      index: "users"
```

### Plugin Lifecycle Management

The external plugin system provides complete lifecycle management:

1. **Configuration**: Add plugin metadata and requirements
2. **Installation**: Install PyPI packages automatically
3. **Discovery**: Automatic plugin discovery and registration
4. **Usage**: Use plugins in pipeline configurations
5. **Updates**: Update plugins through standard pip commands
6. **Removal**: Uninstall packages and remove configurations

### Best Practices for External Plugin Management

1. **Use Descriptive Names**: Choose clear, descriptive plugin names
2. **Version Management**: Use semantic versioning for plugin versions
3. **API Compatibility**: Ensure plugins use compatible API versions
4. **Documentation**: Provide comprehensive plugin descriptions
5. **Testing**: Test plugins thoroughly before publishing to PyPI
6. **Dependencies**: Minimize external dependencies to reduce conflicts

### Troubleshooting External Plugins

#### Common Issues

1. **Plugin Not Found**
   - Check if plugin is configured in external_plugins.yml
   - Verify package name matches PyPI package
   - Ensure plugin type is correct

2. **Installation Failures**
   - Check internet connectivity
   - Verify PyPI package exists
   - Check for dependency conflicts

3. **Plugin Discovery Issues**
   - Restart Santiq after installation
   - Check plugin entry point configuration
   - Verify API version compatibility

#### Debug Commands

```bash
# Check plugin status
santiq plugin list --external

# Verify package installation
pip list | grep santiq-plugin

# Check plugin discovery
santiq plugin info plugin_name
```

## Best Practices

### 1. Error Handling

Always handle errors gracefully:

```python
def extract(self) -> pd.DataFrame:
    """Extract data with proper error handling."""
    try:
        data = self._fetch_data()
        return pd.DataFrame(data)
    except ConnectionError as e:
        raise PluginError(f"Failed to connect to data source: {e}")
    except Exception as e:
        raise PluginError(f"Unexpected error during extraction: {e}")
```

### 2. Logging

Add appropriate logging:

```python
import logging

logger = logging.getLogger(__name__)

def extract(self) -> pd.DataFrame:
    """Extract data with logging."""
    logger.info(f"Starting data extraction from {self.config['source_url']}")
    
    data = self._fetch_data()
    logger.info(f"Extracted {len(data)} records")
    
    return pd.DataFrame(data)
```

### 3. Configuration Validation

Always validate configuration thoroughly:

```python
def _validate_config(self) -> None:
    """Comprehensive configuration validation."""
    # Check required parameters
    required_params = ["source_url", "api_key"]
    for param in required_params:
        if param not in self.config:
            raise ValueError(f"Missing required parameter: {param}")
    
    # Validate URL format
    import re
    url_pattern = r'^https?://.+'
    if not re.match(url_pattern, self.config["source_url"]):
        raise ValueError("source_url must be a valid HTTP/HTTPS URL")
    
    # Validate API key format
    if len(self.config["api_key"]) < 10:
        raise ValueError("api_key must be at least 10 characters long")
```

### 4. Performance Considerations

Optimize for performance:

```python
def extract(self) -> pd.DataFrame:
    """Optimized data extraction."""
    # Use chunking for large datasets
    chunk_size = self.config.get("chunk_size", 1000)
    
    all_data = []
    for chunk in self._fetch_data_in_chunks(chunk_size):
        all_data.extend(chunk)
    
    return pd.DataFrame(all_data)
```

### 5. Documentation

Provide comprehensive documentation:

```python
class MyCustomExtractor(ExtractorPlugin):
    """
    Custom data extractor for MyService API.
    
    This plugin extracts data from the MyService REST API and returns
    it as a pandas DataFrame.
    
    Configuration:
        source_url (str): The API endpoint URL (required)
        api_key (str): API authentication key (required)
        timeout (int): Request timeout in seconds (default: 30)
        chunk_size (int): Number of records per request (default: 1000)
    
    Returns:
        DataFrame with columns: id, name, value, created_at
    """
```

## Troubleshooting

### Common Issues

1. **Plugin Not Found**
   - Check entry point configuration
   - Verify plugin is installed correctly
   - Check plugin name matches entry point

2. **Import Errors**
   - Ensure all dependencies are installed
   - Check Python path configuration
   - Verify import statements

3. **Configuration Errors**
   - Validate all required parameters
   - Check parameter types and formats
   - Test configuration validation

4. **Performance Issues**
   - Use chunking for large datasets
   - Implement connection pooling
   - Add caching where appropriate

### Debugging Tips

1. **Enable Debug Logging**
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

2. **Test Plugin Discovery**
   ```python
   from santiq.core.plugin_manager import PluginManager
   pm = PluginManager()
   plugins = pm.discover_plugins()
   print(plugins)
   ```

3. **Check Entry Points**
   ```python
   import importlib.metadata
   eps = importlib.metadata.entry_points()
   print(eps.select(group="santiq.extractors"))
   ```

## Examples

### Complete Extractor Example

```python
import pandas as pd
import requests
from typing import Dict, Any
from santiq.plugins.base.extractor import ExtractorPlugin

class APIExtractor(ExtractorPlugin):
    """Extract data from REST API endpoints."""
    
    __plugin_name__ = "API Extractor"
    __api_version__ = "1.0"
    __description__ = "Extracts data from REST API endpoints"
    __version__ = "1.0.0"
    
    def _validate_config(self) -> None:
        """Validate plugin configuration."""
        required_params = ["base_url", "endpoint"]
        for param in required_params:
            if param not in self.config:
                raise ValueError(f"Missing required parameter: {param}")
        
        # Validate URL
        import re
        url_pattern = r'^https?://.+'
        if not re.match(url_pattern, self.config["base_url"]):
            raise ValueError("base_url must be a valid HTTP/HTTPS URL")
    
    def extract(self) -> pd.DataFrame:
        """Extract data from API."""
        base_url = self.config["base_url"]
        endpoint = self.config["endpoint"]
        timeout = self.config.get("timeout", 30)
        
        url = f"{base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        
        try:
            response = requests.get(url, timeout=timeout)
            response.raise_for_status()
            
            data = response.json()
            return pd.DataFrame(data)
            
        except requests.RequestException as e:
            raise PluginError(f"API request failed: {e}")
        except ValueError as e:
            raise PluginError(f"Invalid JSON response: {e}")
    
    def get_schema_info(self) -> Dict[str, Any]:
        """Return schema information."""
        return {
            "columns": ["id", "name", "value"],
            "data_types": {
                "id": "int64",
                "name": "object",
                "value": "float64"
            },
            "estimated_rows": 100
        }
```

### Complete Transformer Example

```python
import pandas as pd
import re
from typing import Dict, Any, List
from santiq.plugins.base.transformer import TransformerPlugin, TransformResult

class DataCleaner(TransformerPlugin):
    """Clean and validate data."""
    
    __plugin_name__ = "Data Cleaner"
    __api_version__ = "1.0"
    __description__ = "Cleans and validates data with configurable rules"
    __version__ = "1.0.0"
    
    def transform(self, data: pd.DataFrame) -> TransformResult:
        """Transform the data."""
        transformed_data = data.copy()
        applied_fixes = []
        
        # Remove duplicates
        if self.config.get("remove_duplicates", False):
            original_count = len(transformed_data)
            transformed_data = transformed_data.drop_duplicates()
            removed_count = original_count - len(transformed_data)
            
            if removed_count > 0:
                applied_fixes.append({
                    "fix_type": "remove_duplicates",
                    "description": f"Removed {removed_count} duplicate rows",
                    "rows_affected": removed_count
                })
        
        # Clean email addresses
        if self.config.get("clean_emails", False) and "email" in transformed_data.columns:
            cleaned_count = self._clean_emails(transformed_data)
            if cleaned_count > 0:
                applied_fixes.append({
                    "fix_type": "clean_emails",
                    "description": f"Cleaned {cleaned_count} email addresses",
                    "rows_affected": cleaned_count
                })
        
        # Standardize names
        if self.config.get("standardize_names", False) and "name" in transformed_data.columns:
            standardized_count = self._standardize_names(transformed_data)
            if standardized_count > 0:
                applied_fixes.append({
                    "fix_type": "standardize_names",
                    "description": f"Standardized {standardized_count} names",
                    "rows_affected": standardized_count
                })
        
        return TransformResult(transformed_data, applied_fixes, {"cleaner_version": "1.0.0"})
    
    def _clean_emails(self, data: pd.DataFrame) -> int:
        """Clean email addresses."""
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        # Convert to lowercase and strip whitespace
        data["email"] = data["email"].str.lower().str.strip()
        
        # Mark invalid emails as null
        valid_emails = data["email"].str.match(email_pattern, na=False)
        invalid_count = (~valid_emails).sum()
        
        if invalid_count > 0:
            data.loc[~valid_emails, "email"] = None
        
        return invalid_count
    
    def _standardize_names(self, data: pd.DataFrame) -> int:
        """Standardize name formats."""
        original_names = data["name"].copy()
        data["name"] = data["name"].str.title()
        
        changes = (original_names != data["name"]).sum()
        return changes
```

### Complete Loader Example

```python
import pandas as pd
import sqlite3
from typing import Dict, Any
from santiq.plugins.base.loader import LoaderPlugin, LoadResult

class SQLiteLoader(LoaderPlugin):
    """Load data to SQLite database."""
    
    __plugin_name__ = "SQLite Loader"
    __api_version__ = "1.0"
    __description__ = "Loads data to SQLite database"
    __version__ = "1.0.0"
    
    def _validate_config(self) -> None:
        """Validate plugin configuration."""
        required_params = ["database_path", "table_name"]
        for param in required_params:
            if param not in self.config:
                raise ValueError(f"Missing required parameter: {param}")
    
    def load(self, data: pd.DataFrame) -> LoadResult:
        """Load data to SQLite database."""
        database_path = self.config["database_path"]
        table_name = self.config["table_name"]
        if_exists = self.config.get("if_exists", "replace")
        
        try:
            # Create connection
            conn = sqlite3.connect(database_path)
            
            # Load data
            data.to_sql(
                table_name,
                conn,
                if_exists=if_exists,
                index=False
            )
            
            # Get row count
            cursor = conn.cursor()
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            row_count = cursor.fetchone()[0]
            
            conn.close()
            
            return LoadResult(
                success=True,
                rows_loaded=row_count,
                metadata={
                    "database": database_path,
                    "table": table_name,
                    "if_exists": if_exists
                }
            )
            
        except Exception as e:
            return LoadResult(
                success=False,
                rows_loaded=0,
                metadata={"error": str(e)}
            )
    
    def supports_incremental(self) -> bool:
        """Check if this loader supports incremental loading."""
        return True
```

## Conclusion

This guide has covered the essential aspects of developing external plugins for Santiq. Remember to:

1. **Follow the interface**: Implement all required methods
2. **Validate configuration**: Always validate input parameters
3. **Handle errors gracefully**: Provide meaningful error messages
4. **Test thoroughly**: Create comprehensive unit and integration tests
5. **Document well**: Provide clear documentation and examples
6. **Optimize performance**: Consider performance implications
7. **Follow best practices**: Use logging, error handling, and validation

For more information, refer to:
- [Santiq Documentation](https://github.com/your-org/santiq)
- [Plugin API Reference](https://github.com/your-org/santiq/docs/api.md)
- [Community Plugins](https://github.com/your-org/santiq-plugins)

Happy plugin development!

