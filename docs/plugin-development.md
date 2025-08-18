# Plugin Development Guide

Complete guide to creating custom plugins for Santiq. Learn how to extend Santiq's functionality with your own extractors, profilers, transformers, and loaders.

## 📋 Table of Contents

1. [Overview](#overview)
2. [Plugin Architecture](#plugin-architecture)
3. [Plugin Types](#plugin-types)
4. [Creating Your First Plugin](#creating-your-first-plugin)
5. [Plugin Development Workflow](#plugin-development-workflow)
6. [Advanced Plugin Features](#advanced-plugin-features)
7. [Testing Plugins](#testing-plugins)
8. [Distributing Plugins](#distributing-plugins)
9. [Best Practices](#best-practices)

## 🎯 Overview

Santiq's plugin architecture allows you to extend the platform with custom functionality. Every component in Santiq is a plugin, making it highly modular and extensible.

### Why Create Plugins?

- **Custom Data Sources**: Extract data from proprietary systems
- **Specialized Transformations**: Implement business-specific data processing
- **Custom Destinations**: Load data to specialized systems
- **Domain-Specific Profiling**: Create data quality checks for your domain
- **Integration**: Connect with existing tools and workflows

### Plugin Types

1. **Extractors**: Read data from sources
2. **Profilers**: Analyze data quality
3. **Transformers**: Clean and transform data
4. **Loaders**: Write data to destinations

## 🏗️ Plugin Architecture

### Base Classes

All plugins inherit from base classes that define the interface:

```python
from santiq.plugins.base.extractor import ExtractorPlugin
from santiq.plugins.base.profiler import ProfilerPlugin
from santiq.plugins.base.transformer import TransformerPlugin
from santiq.plugins.base.loader import LoaderPlugin
```

### Plugin Lifecycle

1. **Discovery**: Santiq finds and loads plugins
2. **Configuration**: Plugin receives configuration parameters
3. **Execution**: Plugin performs its operation
4. **Cleanup**: Plugin releases resources

### Plugin Metadata

Every plugin must define metadata:

```python
__plugin_name__ = "My Plugin"
__version__ = "1.0.0"
__description__ = "Description of what this plugin does"
__api_version__ = "1.0"
```

## 🔌 Plugin Types

### Extractor Plugins

Extractors read data from sources and return pandas DataFrames.

**Required Methods**:
- `extract()`: Extract data and return DataFrame

**Optional Methods**:
- `get_schema_info()`: Return schema information

```python
class MyExtractor(ExtractorPlugin):
    def extract(self) -> pd.DataFrame:
        # Extract data from source
        return data
```

### Profiler Plugins

Profilers analyze data quality and return issues and suggestions.

**Required Methods**:
- `profile(data: pd.DataFrame) -> ProfileResult`

```python
class MyProfiler(ProfilerPlugin):
    def profile(self, data: pd.DataFrame) -> ProfileResult:
        # Analyze data and return results
        return ProfileResult(issues, summary, suggestions)
```

### Transformer Plugins

Transformers clean and transform data.

**Required Methods**:
- `transform(data: pd.DataFrame) -> TransformResult`
- `suggest_fixes(data: pd.DataFrame, issues: List[Dict]) -> List[Dict]`

```python
class MyTransformer(TransformerPlugin):
    def transform(self, data: pd.DataFrame) -> TransformResult:
        # Transform data
        return TransformResult(transformed_data, applied_fixes)
    
    def suggest_fixes(self, data: pd.DataFrame, issues: List[Dict]) -> List[Dict]:
        # Suggest fixes for issues
        return suggestions
```

### Loader Plugins

Loaders write data to destinations.

**Required Methods**:
- `load(data: pd.DataFrame) -> LoadResult`

```python
class MyLoader(LoaderPlugin):
    def load(self, data: pd.DataFrame) -> LoadResult:
        # Load data to destination
        return LoadResult(success, rows_loaded, metadata)
```

## 🚀 Creating Your First Plugin

### Step 1: Set Up Development Environment

```bash
# Clone Santiq repository
git clone https://github.com/yourusername/santiq.git
cd santiq

# Install in development mode
pip install -e ".[dev]"

# Create plugin directory
mkdir my_plugin
cd my_plugin
```

### Step 2: Create Plugin Structure

```
my_plugin/
├── my_plugin/
│   ├── __init__.py
│   ├── extractor.py
│   ├── profiler.py
│   ├── transformer.py
│   └── loader.py
├── tests/
│   ├── __init__.py
│   ├── test_extractor.py
│   ├── test_profiler.py
│   ├── test_transformer.py
│   └── test_loader.py
├── setup.py
├── pyproject.toml
└── README.md
```

### Step 3: Create a Simple Extractor

```python
# my_plugin/extractor.py
import pandas as pd
from santiq.plugins.base.extractor import ExtractorPlugin

class SimpleExtractor(ExtractorPlugin):
    """A simple extractor that creates sample data."""
    
    __plugin_name__ = "Simple Extractor"
    __version__ = "1.0.0"
    __description__ = "Creates sample data for testing"
    __api_version__ = "1.0"
    
    def _validate_config(self) -> None:
        """Validate configuration."""
        if 'rows' not in self.config:
            raise ValueError("Simple Extractor requires 'rows' parameter")
    
    def extract(self) -> pd.DataFrame:
        """Extract sample data."""
        rows = self.config.get('rows', 10)
        
        # Create sample data
        data = {
            'id': range(1, rows + 1),
            'name': [f'User {i}' for i in range(1, rows + 1)],
            'email': [f'user{i}@example.com' for i in range(1, rows + 1)],
            'age': [20 + (i % 50) for i in range(1, rows + 1)]
        }
        
        return pd.DataFrame(data)
    
    def get_schema_info(self) -> Dict[str, Any]:
        """Get schema information."""
        return {
            "columns": ["id", "name", "email", "age"],
            "estimated_rows": self.config.get('rows', 10),
            "data_types": {
                "id": "int64",
                "name": "object",
                "email": "object",
                "age": "int64"
            }
        }
```

### Step 4: Create Plugin Manifest

```yaml
# plugin.yml
name: "simple_extractor"
entry_point: "my_plugin.extractor:SimpleExtractor"
type: "extractor"
version: "1.0.0"
api_version: "1.0"
description: "A simple extractor that creates sample data"
author: "Your Name"
license: "MIT"
```

### Step 5: Test Your Plugin

```python
# test_extractor.py
import pytest
import pandas as pd
from my_plugin.extractor import SimpleExtractor

def test_simple_extractor():
    # Create plugin instance
    extractor = SimpleExtractor()
    
    # Configure plugin
    extractor.setup({'rows': 5})
    
    # Extract data
    data = extractor.extract()
    
    # Assertions
    assert isinstance(data, pd.DataFrame)
    assert len(data) == 5
    assert list(data.columns) == ['id', 'name', 'email', 'age']
```

## 🔄 Plugin Development Workflow

### 1. Local Development

```bash
# Create plugin directory in Santiq
mkdir -p santiq/plugins/my_plugin
cd santiq/plugins/my_plugin

# Create your plugin files
touch __init__.py
touch my_extractor.py
touch plugin.yml
```

### 2. Testing with Santiq

```bash
# Test plugin discovery
santiq plugin list --local-dir ./santiq/plugins

# Test plugin with pipeline
santiq run pipeline test_config.yml --plugin-dir ./santiq/plugins
```

### 3. Configuration Testing

```yaml
# test_config.yml
name: "Test Plugin Pipeline"
description: "Test my custom plugin"

extractor:
  plugin: simple_extractor
  params:
    rows: 10

profilers:
  - plugin: basic_profiler
    params: {}

transformers:
  - plugin: basic_cleaner
    params:
      drop_duplicates: true

loaders:
  - plugin: csv_loader
    params:
      path: "output.csv"
```

## 🚀 Advanced Plugin Features

### Configuration Validation

```python
def _validate_config(self) -> None:
    """Validate plugin configuration."""
    required_params = ['path', 'format']
    for param in required_params:
        if param not in self.config:
            raise ValueError(f"Missing required parameter: {param}")
    
    # Validate parameter types
    if not isinstance(self.config.get('timeout', 30), int):
        raise ValueError("timeout must be an integer")
    
    # Validate parameter ranges
    timeout = self.config.get('timeout', 30)
    if timeout < 1 or timeout > 3600:
        raise ValueError("timeout must be between 1 and 3600 seconds")
```

### Error Handling

```python
def extract(self) -> pd.DataFrame:
    """Extract data with proper error handling."""
    try:
        # Attempt extraction
        data = self._extract_from_source()
        return data
    except FileNotFoundError:
        raise Exception(f"Source file not found: {self.config['path']}")
    except PermissionError:
        raise Exception(f"Permission denied accessing: {self.config['path']}")
    except Exception as e:
        raise Exception(f"Extraction failed: {str(e)}")
```

### Resource Management

```python
def setup(self, config: Dict[str, Any]) -> None:
    """Setup plugin with resource management."""
    super().setup(config)
    
    # Initialize connections
    self.connection = self._create_connection()
    
def teardown(self) -> None:
    """Cleanup resources."""
    if hasattr(self, 'connection'):
        self.connection.close()
        del self.connection
```

### Logging

```python
import logging

class MyPlugin(ExtractorPlugin):
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(f"santiq.plugin.{self.__class__.__name__}")
    
    def extract(self) -> pd.DataFrame:
        self.logger.info("Starting data extraction")
        # ... extraction logic ...
        self.logger.info(f"Extracted {len(data)} rows")
        return data
```

### Progress Reporting

```python
def extract(self) -> pd.DataFrame:
    """Extract data with progress reporting."""
    total_rows = self._get_total_rows()
    
    # Report progress
    if hasattr(self, 'progress_callback'):
        self.progress_callback(0, total_rows)
    
    data = []
    for i, row in enumerate(self._iterate_rows()):
        data.append(row)
        
        # Report progress every 1000 rows
        if i % 1000 == 0 and hasattr(self, 'progress_callback'):
            self.progress_callback(i, total_rows)
    
    return pd.DataFrame(data)
```

## 🧪 Testing Plugins

### Unit Testing

```python
# test_my_plugin.py
import pytest
import pandas as pd
from unittest.mock import Mock, patch
from my_plugin.extractor import MyExtractor

class TestMyExtractor:
    def setup_method(self):
        self.extractor = MyExtractor()
    
    def test_config_validation(self):
        """Test configuration validation."""
        # Test missing required parameter
        with pytest.raises(ValueError, match="Missing required parameter"):
            self.extractor.setup({})
        
        # Test valid configuration
        self.extractor.setup({'path': 'test.csv', 'format': 'csv'})
        assert self.extractor.config['path'] == 'test.csv'
    
    def test_extract_data(self):
        """Test data extraction."""
        self.extractor.setup({'path': 'test.csv', 'format': 'csv'})
        
        with patch('my_plugin.extractor.pd.read_csv') as mock_read:
            mock_read.return_value = pd.DataFrame({'col1': [1, 2, 3]})
            
            result = self.extractor.extract()
            
            assert isinstance(result, pd.DataFrame)
            assert len(result) == 3
            mock_read.assert_called_once_with('test.csv')
    
    def test_error_handling(self):
        """Test error handling."""
        self.extractor.setup({'path': 'nonexistent.csv', 'format': 'csv'})
        
        with pytest.raises(Exception, match="Source file not found"):
            self.extractor.extract()
```

### Integration Testing

```python
# test_integration.py
def test_plugin_integration():
    """Test plugin integration with Santiq."""
    from santiq.core.engine import ETLEngine
    
    # Create engine with plugin directory
    engine = ETLEngine(local_plugin_dirs=['./plugins'])
    
    # Test plugin discovery
    plugins = engine.list_plugins()
    assert 'my_extractor' in [p['name'] for p in plugins['extractor']]
    
    # Test plugin execution
    config = {
        'extractor': {
            'plugin': 'my_extractor',
            'params': {'path': 'test.csv', 'format': 'csv'}
        },
        'loaders': [{
            'plugin': 'csv_loader',
            'params': {'path': 'output.csv'}
        }]
    }
    
    result = engine.run_pipeline_from_config(config)
    assert result['success'] == True
```

### Performance Testing

```python
import time

def test_performance():
    """Test plugin performance."""
    extractor = MyExtractor()
    extractor.setup({'path': 'large_file.csv', 'format': 'csv'})
    
    start_time = time.time()
    data = extractor.extract()
    end_time = time.time()
    
    execution_time = end_time - start_time
    rows_per_second = len(data) / execution_time
    
    print(f"Extracted {len(data)} rows in {execution_time:.2f} seconds")
    print(f"Performance: {rows_per_second:.0f} rows/second")
    
    # Assert performance requirements
    assert execution_time < 60  # Should complete within 60 seconds
    assert rows_per_second > 1000  # Should process at least 1000 rows/second
```

## 📦 Distributing Plugins

### Package Structure

```
my-santiq-plugin/
├── my_santiq_plugin/
│   ├── __init__.py
│   ├── extractor.py
│   ├── profiler.py
│   ├── transformer.py
│   └── loader.py
├── tests/
├── setup.py
├── pyproject.toml
├── README.md
└── LICENSE
```

### Setup Configuration

```python
# setup.py
from setuptools import setup, find_packages

setup(
    name="santiq-plugin-my",
    version="1.0.0",
    description="My custom Santiq plugin",
    author="Your Name",
    author_email="your.email@example.com",
    packages=find_packages(),
    install_requires=[
        "santiq>=0.1.5",
        "pandas>=2.0.0",
    ],
    entry_points={
        "santiq.extractors": [
            "my_extractor = my_santiq_plugin.extractor:MyExtractor",
        ],
        "santiq.profilers": [
            "my_profiler = my_santiq_plugin.profiler:MyProfiler",
        ],
        "santiq.transformers": [
            "my_transformer = my_santiq_plugin.transformer:MyTransformer",
        ],
        "santiq.loaders": [
            "my_loader = my_santiq_plugin.loader:MyLoader",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
    ],
)
```

### PyPI Distribution

```bash
# Build package
python setup.py sdist bdist_wheel

# Upload to PyPI
twine upload dist/*

# Install from PyPI
pip install santiq-plugin-my
```

### Local Distribution

```bash
# Install from local directory
pip install -e .

# Use with Santiq
santiq plugin list
```

## 📊 Best Practices

### Plugin Design

1. **Single Responsibility**: Each plugin should do one thing well
2. **Configuration Driven**: Use configuration for flexibility
3. **Error Handling**: Provide clear error messages
4. **Resource Management**: Clean up resources properly
5. **Documentation**: Document all parameters and behavior

### Performance

1. **Memory Efficiency**: Handle large datasets efficiently
2. **Progress Reporting**: Report progress for long operations
3. **Caching**: Cache expensive operations when appropriate
4. **Parallel Processing**: Use parallel processing when possible

### Testing

1. **Unit Tests**: Test individual methods
2. **Integration Tests**: Test with Santiq
3. **Performance Tests**: Test with realistic data sizes
4. **Error Tests**: Test error conditions

### Documentation

```python
class MyExtractor(ExtractorPlugin):
    """Extract data from MySystem.
    
    This plugin extracts data from MySystem using the provided
    connection parameters.
    
    Configuration Parameters:
        host (str): MySystem host address (required)
        port (int): MySystem port (default: 8080)
        username (str): MySystem username (required)
        password (str): MySystem password (required)
        database (str): Database name (required)
        query (str): SQL query to execute (required)
        timeout (int): Connection timeout in seconds (default: 30)
    
    Example Configuration:
        {
            "host": "mysystem.example.com",
            "port": 8080,
            "username": "user",
            "password": "pass",
            "database": "mydb",
            "query": "SELECT * FROM users"
        }
    """
```

### Versioning

1. **Semantic Versioning**: Use semantic versioning (MAJOR.MINOR.PATCH)
2. **API Compatibility**: Maintain API compatibility within major versions
3. **Deprecation**: Deprecate features gracefully
4. **Migration**: Provide migration guides for breaking changes

## 📚 Additional Resources

- **[Getting Started Guide](getting-started.md)** - Quick start tutorial
- **[User Guide](user-guide.md)** - Comprehensive usage instructions
- **[Configuration Reference](configuration.md)** - Configuration options
- **[CLI Reference](cli-reference.md)** - Command-line interface
- **[API Reference](api-reference.md)** - Core API documentation
- **[Examples](../examples/)** - Sample plugins and configurations

---

**Ready to create your first plugin?** Start with the [Getting Started Guide](getting-started.md) to understand Santiq basics, then follow this guide to build your custom plugin!
