# API Reference

Complete API documentation for Santiq's core components, classes, and interfaces.

## 📋 Table of Contents

1. [Core Engine](#core-engine)
2. [Pipeline Management](#pipeline-management)
3. [Plugin System](#plugin-system)
4. [Configuration Management](#configuration-management)
5. [Audit System](#audit-system)
6. [Data Models](#data-models)
7. [Exceptions](#exceptions)

## 🚀 Core Engine

### ETLEngine

The main engine that orchestrates ETL pipeline execution.

```python
from santiq.core.engine import ETLEngine
```

#### Constructor

```python
ETLEngine(
    local_plugin_dirs: Optional[List[str]] = None,
    audit_log_path: Optional[str] = None,
    config_manager: Optional[ConfigManager] = None
)
```

**Parameters**:
- `local_plugin_dirs`: List of directories containing local plugins
- `audit_log_path`: Path to audit log file
- `config_manager`: Configuration manager instance

#### Methods

##### run_pipeline

Execute a pipeline from configuration file.

```python
def run_pipeline(
    self,
    config_path: str,
    mode: str = "manual",
    plugin_dirs: Optional[List[str]] = None
) -> Dict[str, Any]
```

**Parameters**:
- `config_path`: Path to pipeline configuration file
- `mode`: Execution mode ("manual", "half-auto", "controlled-auto")
- `plugin_dirs`: Additional plugin directories

**Returns**: Dictionary with execution results

**Example**:
```python
engine = ETLEngine()
result = engine.run_pipeline("pipeline.yml", mode="manual")
print(f"Success: {result['success']}")
print(f"Rows processed: {result['rows_processed']}")
```

##### run_pipeline_from_config

Execute a pipeline from configuration dictionary.

```python
def run_pipeline_from_config(
    self,
    config: Dict[str, Any],
    mode: str = "manual"
) -> Dict[str, Any]
```

**Parameters**:
- `config`: Pipeline configuration dictionary
- `mode`: Execution mode

**Returns**: Dictionary with execution results

##### list_plugins

List available plugins.

```python
def list_plugins(
    self,
    plugin_type: Optional[str] = None,
    include_local: bool = True
) -> Dict[str, List[Dict[str, Any]]]
```

**Parameters**:
- `plugin_type`: Filter by plugin type
- `include_local`: Include local plugins

**Returns**: Dictionary mapping plugin types to plugin lists

##### install_external_plugin

Install an external plugin package.

```python
def install_external_plugin(
    self,
    package_name: str,
    upgrade: bool = False
) -> bool
```

**Parameters**:
- `package_name`: PyPI package name
- `upgrade`: Upgrade if already installed

**Returns**: Success status

##### get_pipeline_history

Get pipeline execution history.

```python
def get_pipeline_history(
    self,
    pipeline_id: Optional[str] = None,
    limit: int = 10
) -> List[Dict[str, Any]]
```

**Parameters**:
- `pipeline_id`: Specific pipeline ID
- `limit`: Number of entries to return

**Returns**: List of audit events

## 🔄 Pipeline Management

### Pipeline

Manages the execution of an ETL pipeline.

```python
from santiq.core.pipeline import Pipeline
```

#### Constructor

```python
Pipeline(
    config: PipelineConfig,
    engine: ETLEngine
)
```

#### Methods

##### execute

Execute the pipeline.

```python
def execute(self, mode: str = "manual") -> Dict[str, Any]
```

**Parameters**:
- `mode`: Execution mode

**Returns**: Execution results

### PipelineContext

Holds execution state and data during pipeline execution.

```python
from santiq.core.pipeline import PipelineContext
```

#### Attributes

- `data`: Current data DataFrame
- `metadata`: Pipeline metadata
- `issues`: Data quality issues
- `suggestions`: Suggested fixes
- `applied_fixes`: Applied transformations

#### Methods

##### add_issue

Add a data quality issue.

```python
def add_issue(
    self,
    issue_type: str,
    description: str,
    severity: str = "warning",
    column: Optional[str] = None,
    row_indices: Optional[List[int]] = None
) -> None
```

##### add_suggestion

Add a suggested fix.

```python
def add_suggestion(
    self,
    issue_type: str,
    description: str,
    transformer: str,
    params: Dict[str, Any]
) -> None
```

## 🔌 Plugin System

### PluginManager

Manages plugin discovery, loading, and instantiation.

```python
from santiq.core.plugin_manager import PluginManager
```

#### Constructor

```python
PluginManager(
    local_plugin_dirs: Optional[List[str]] = None
)
```

#### Methods

##### discover_plugins

Discover available plugins.

```python
def discover_plugins(self) -> Dict[str, List[Dict[str, Any]]]
```

**Returns**: Dictionary mapping plugin types to plugin information

##### load_plugin

Load a plugin by name and type.

```python
def load_plugin(
    self,
    plugin_name: str,
    plugin_type: str
) -> Any
```

**Parameters**:
- `plugin_name`: Name of the plugin
- `plugin_type`: Type of plugin

**Returns**: Plugin class

##### create_plugin_instance

Create a plugin instance with configuration.

```python
def create_plugin_instance(
    self,
    plugin_name: str,
    plugin_type: str,
    config: Dict[str, Any]
) -> Any
```

**Parameters**:
- `plugin_name`: Name of the plugin
- `plugin_type`: Type of plugin
- `config`: Plugin configuration

**Returns**: Plugin instance

### Base Plugin Classes

#### ExtractorPlugin

Base class for all extractor plugins.

```python
from santiq.plugins.base.extractor import ExtractorPlugin
```

**Required Methods**:
- `extract() -> pd.DataFrame`

**Optional Methods**:
- `get_schema_info() -> Dict[str, Any]`

#### ProfilerPlugin

Base class for all profiler plugins.

```python
from santiq.plugins.base.profiler import ProfilerPlugin
```

**Required Methods**:
- `profile(data: pd.DataFrame) -> ProfileResult`

#### TransformerPlugin

Base class for all transformer plugins.

```python
from santiq.plugins.base.transformer import TransformerPlugin
```

**Required Methods**:
- `transform(data: pd.DataFrame) -> TransformResult`
- `suggest_fixes(data: pd.DataFrame, issues: List[Dict]) -> List[Dict]`

#### LoaderPlugin

Base class for all loader plugins.

```python
from santiq.plugins.base.loader import LoaderPlugin
```

**Required Methods**:
- `load(data: pd.DataFrame) -> LoadResult`

## ⚙️ Configuration Management

### ConfigManager

Manages pipeline and plugin configurations.

```python
from santiq.core.config import ConfigManager
```

#### Constructor

```python
ConfigManager()
```

#### Methods

##### load_config

Load configuration from file.

```python
def load_config(self, config_path: str) -> PipelineConfig
```

**Parameters**:
- `config_path`: Path to configuration file

**Returns**: Pipeline configuration object

##### validate_config

Validate configuration.

```python
def validate_config(self, config: Dict[str, Any]) -> bool
```

**Parameters**:
- `config`: Configuration dictionary

**Returns**: Validation result

##### substitute_env_vars

Substitute environment variables in configuration.

```python
def substitute_env_vars(self, config: Dict[str, Any]) -> Dict[str, Any]
```

**Parameters**:
- `config`: Configuration dictionary

**Returns**: Configuration with substituted variables

### Configuration Models

#### PipelineConfig

Pipeline configuration model.

```python
from santiq.core.config import PipelineConfig
```

**Attributes**:
- `name`: Pipeline name
- `description`: Pipeline description
- `version`: Pipeline version
- `extractor`: Extractor configuration
- `profilers`: List of profiler configurations
- `transformers`: List of transformer configurations
- `loaders`: List of loader configurations
- `cache_intermediate_results`: Cache intermediate results
- `max_memory_mb`: Maximum memory usage
- `temp_dir`: Temporary directory
- `parallel_execution`: Enable parallel execution
- `log_level`: Logging level
- `on_error`: Error handling strategy
- `timeout`: Plugin timeout

#### PluginConfig

Plugin configuration model.

```python
from santiq.core.config import PluginConfig
```

**Attributes**:
- `plugin`: Plugin name
- `params`: Plugin parameters
- `on_error`: Error handling strategy
- `enabled`: Enable/disable plugin
- `timeout`: Plugin timeout

## 📊 Audit System

### AuditLogger

Manages audit logging for pipeline execution.

```python
from santiq.core.audit import AuditLogger
```

#### Constructor

```python
AuditLogger(audit_log_path: str)
```

#### Methods

##### log_event

Log an audit event.

```python
def log_event(
    self,
    event_type: str,
    pipeline_id: str,
    plugin_name: Optional[str] = None,
    status: str = "success",
    details: Optional[Dict[str, Any]] = None
) -> None
```

**Parameters**:
- `event_type`: Type of event
- `pipeline_id`: Pipeline identifier
- `plugin_name`: Plugin name (if applicable)
- `status`: Event status
- `details`: Additional event details

##### get_pipeline_events

Get events for a specific pipeline.

```python
def get_pipeline_events(
    self,
    pipeline_id: str,
    limit: int = 100
) -> List[AuditEvent]
```

**Parameters**:
- `pipeline_id`: Pipeline identifier
- `limit`: Maximum number of events

**Returns**: List of audit events

##### get_recent_events

Get recent events across all pipelines.

```python
def get_recent_events(
    self,
    limit: int = 50
) -> List[AuditEvent]
```

**Parameters**:
- `limit`: Maximum number of events

**Returns**: List of audit events

### AuditEvent

Audit event model.

```python
from santiq.core.audit import AuditEvent
```

**Attributes**:
- `timestamp`: Event timestamp
- `event_type`: Type of event
- `pipeline_id`: Pipeline identifier
- `plugin_name`: Plugin name (if applicable)
- `status`: Event status
- `details`: Additional event details

## 📋 Data Models

### ProfileResult

Result from data profiling.

```python
from dataclasses import dataclass
from typing import List, Dict, Any

@dataclass
class ProfileResult:
    issues: List[Dict[str, Any]]
    summary: Dict[str, Any]
    suggestions: List[Dict[str, Any]]
```

### TransformResult

Result from data transformation.

```python
@dataclass
class TransformResult:
    data: pd.DataFrame
    applied_fixes: List[Dict[str, Any]]
    metadata: Dict[str, Any]
```

### LoadResult

Result from data loading.

```python
@dataclass
class LoadResult:
    success: bool
    rows_loaded: int
    metadata: Dict[str, Any]
```

## ❌ Exceptions

### SantiqException

Base exception for Santiq.

```python
from santiq.core.exceptions import SantiqException
```

### ConfigurationError

Configuration-related errors.

```python
from santiq.core.exceptions import ConfigurationError
```

### PluginError

Plugin-related errors.

```python
from santiq.core.exceptions import PluginError
```

### PipelineError

Pipeline execution errors.

```python
from santiq.core.exceptions import PipelineError
```

## 📝 Usage Examples

### Basic Pipeline Execution

```python
from santiq.core.engine import ETLEngine
from santiq.core.config import ConfigManager

# Create engine
engine = ETLEngine()

# Load configuration
config_manager = ConfigManager()
config = config_manager.load_config("pipeline.yml")

# Run pipeline
result = engine.run_pipeline_from_config(config.dict(), mode="manual")

# Check results
if result['success']:
    print(f"Pipeline completed successfully")
    print(f"Rows processed: {result['rows_processed']}")
else:
    print(f"Pipeline failed: {result['error']}")
```

### Custom Plugin Integration

```python
from santiq.core.engine import ETLEngine
from santiq.plugins.base.extractor import ExtractorPlugin
import pandas as pd

# Create custom extractor
class CustomExtractor(ExtractorPlugin):
    __plugin_name__ = "custom_extractor"
    __version__ = "1.0.0"
    __description__ = "Custom data extractor"
    __api_version__ = "1.0"
    
    def extract(self) -> pd.DataFrame:
        # Custom extraction logic
        return pd.DataFrame({'col1': [1, 2, 3]})

# Create engine with local plugin directory
engine = ETLEngine(local_plugin_dirs=['./plugins'])

# Run pipeline with custom plugin
config = {
    'extractor': {
        'plugin': 'custom_extractor',
        'params': {}
    },
    'loaders': [{
        'plugin': 'csv_loader',
        'params': {'path': 'output.csv'}
    }]
}

result = engine.run_pipeline_from_config(config)
```

### Audit Logging

```python
from santiq.core.audit import AuditLogger

# Create audit logger
logger = AuditLogger("audit.log")

# Log pipeline start
logger.log_event(
    event_type="pipeline_start",
    pipeline_id="pipeline_123",
    details={"config_file": "pipeline.yml"}
)

# Log plugin execution
logger.log_event(
    event_type="plugin_start",
    pipeline_id="pipeline_123",
    plugin_name="csv_extractor",
    details={"params": {"path": "data.csv"}}
)

# Get pipeline history
events = logger.get_pipeline_events("pipeline_123")
for event in events:
    print(f"{event.timestamp}: {event.event_type} - {event.status}")
```

### Configuration Management

```python
from santiq.core.config import ConfigManager

# Create config manager
config_manager = ConfigManager()

# Load and validate configuration
config = config_manager.load_config("pipeline.yml")

# Substitute environment variables
config_dict = config_manager.substitute_env_vars(config.dict())

# Validate configuration
if config_manager.validate_config(config_dict):
    print("Configuration is valid")
else:
    print("Configuration validation failed")
```

## 🔧 Advanced Usage

### Custom Plugin Development

```python
from santiq.plugins.base.transformer import TransformerPlugin
from santiq.core.exceptions import PluginError

class AdvancedTransformer(TransformerPlugin):
    __plugin_name__ = "advanced_transformer"
    __version__ = "1.0.0"
    __description__ = "Advanced data transformation"
    __api_version__ = "1.0"
    
    def _validate_config(self) -> None:
        if 'operation' not in self.config:
            raise PluginError("Missing required parameter: operation")
    
    def transform(self, data: pd.DataFrame) -> TransformResult:
        operation = self.config['operation']
        
        if operation == 'uppercase':
            # Convert string columns to uppercase
            for col in data.select_dtypes(include=['object']):
                data[col] = data[col].str.upper()
        elif operation == 'normalize':
            # Normalize numeric columns
            for col in data.select_dtypes(include=['number']):
                data[col] = (data[col] - data[col].mean()) / data[col].std()
        
        return TransformResult(
            data=data,
            applied_fixes=[{"operation": operation}],
            metadata={"transformed_columns": list(data.columns)}
        )
    
    def suggest_fixes(self, data: pd.DataFrame, issues: List[Dict]) -> List[Dict]:
        suggestions = []
        
        for issue in issues:
            if issue['type'] == 'missing_values':
                suggestions.append({
                    'issue_type': 'missing_values',
                    'description': 'Fill missing values',
                    'transformer': 'advanced_transformer',
                    'params': {'operation': 'fill_missing'}
                })
        
        return suggestions
```

### Error Handling

```python
from santiq.core.exceptions import SantiqException, ConfigurationError, PluginError

try:
    engine = ETLEngine()
    result = engine.run_pipeline("pipeline.yml")
except ConfigurationError as e:
    print(f"Configuration error: {e}")
except PluginError as e:
    print(f"Plugin error: {e}")
except SantiqException as e:
    print(f"Santiq error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## 📚 Additional Resources

- **[Getting Started Guide](getting-started.md)** - Quick start tutorial
- **[User Guide](user-guide.md)** - Comprehensive usage instructions
- **[Configuration Reference](configuration.md)** - Configuration options
- **[CLI Reference](cli-reference.md)** - Command-line interface
- **[Plugin Development](plugin-development.md)** - Create custom plugins
- **[Examples](../examples/)** - Sample code and configurations

---

**Need help with a specific API?** Check out the [User Guide](user-guide.md) for practical examples or the [Plugin Development](plugin-development.md) guide for extending Santiq.
