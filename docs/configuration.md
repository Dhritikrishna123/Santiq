# Configuration Reference

Complete reference for Santiq pipeline configuration options, schema definitions, and examples.

## 📋 Table of Contents

1. [Configuration Schema](#configuration-schema)
2. [Global Settings](#global-settings)
3. [Plugin Configuration](#plugin-configuration)
4. [Built-in Plugins](#built-in-plugins)
5. [Environment Variables](#environment-variables)
6. [Configuration Examples](#configuration-examples)
7. [Validation Rules](#validation-rules)

## 🏗️ Configuration Schema

### Root Configuration

```yaml
# Required fields
name: "Pipeline Name"                    # Optional: Pipeline identifier
description: "Description"               # Optional: Pipeline description
version: "1.0.0"                        # Optional: Pipeline version

# Required: Data extraction
extractor:
  plugin: "plugin_name"
  params: {}
  on_error: "stop"                      # stop, continue, retry
  enabled: true
  timeout: 300                          # seconds

# Optional: Data profiling
profilers:
  - plugin: "profiler_name"
    params: {}
    on_error: "stop"
    enabled: true
    timeout: 300

# Optional: Data transformation
transformers:
  - plugin: "transformer_name"
    params: {}
    on_error: "stop"
    enabled: true
    timeout: 300

# Required: Data loading
loaders:
  - plugin: "loader_name"
    params: {}
    on_error: "stop"
    enabled: true
    timeout: 300

# Global settings
cache_intermediate_results: true
max_memory_mb: 1000
temp_dir: "/tmp/santiq"
parallel_execution: false
log_level: "INFO"                       # DEBUG, INFO, WARNING, ERROR, CRITICAL
```

## ⚙️ Global Settings

### Performance Settings

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `cache_intermediate_results` | boolean | `true` | Cache intermediate data between pipeline stages |
| `max_memory_mb` | integer | `None` | Maximum memory usage in MB (None = unlimited) |
| `temp_dir` | string | `None` | Temporary directory for large files |
| `parallel_execution` | boolean | `false` | Enable parallel processing where possible |

### Logging Settings

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `log_level` | string | `"INFO"` | Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL) |

### Error Handling Settings

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `on_error` | string | `"stop"` | Error handling strategy (stop, continue, retry) |
| `timeout` | integer | `None` | Plugin timeout in seconds |

## 🔌 Plugin Configuration

### Plugin Structure

```yaml
plugin: "plugin_name"                   # Required: Plugin identifier
params:                                 # Required: Plugin parameters
  param1: value1
  param2: value2
on_error: "stop"                        # Optional: Error handling
enabled: true                           # Optional: Enable/disable plugin
timeout: 300                            # Optional: Timeout in seconds
```

### Error Handling Strategies

| Strategy | Description |
|----------|-------------|
| `stop` | Stop pipeline execution on error |
| `continue` | Skip failed plugin and continue |
| `retry` | Retry plugin execution (up to 3 times) |

## 📦 Built-in Plugins

### Extractors

#### CSV Extractor (`csv_extractor`)

Extracts data from CSV files using pandas.

```yaml
extractor:
  plugin: csv_extractor
  params:
    path: "data.csv"                    # Required: File path
    sep: ","                            # Optional: Separator (default: ',')
    encoding: "utf-8"                   # Optional: File encoding
    header: 0                           # Optional: Header row (0-based)
    dtype: {}                           # Optional: Column data types
    na_values: []                       # Optional: Values to treat as NaN
    skiprows: 0                         # Optional: Rows to skip
    nrows: null                         # Optional: Number of rows to read
```

**Parameters**:
- `path` (string, required): Path to CSV file
- `sep` (string): Field separator (default: ',')
- `encoding` (string): File encoding (default: 'utf-8')
- `header` (integer): Row number to use as column names
- `dtype` (dict): Data types for specific columns
- `na_values` (list): Values to treat as NaN
- `skiprows` (integer): Number of rows to skip
- `nrows` (integer): Number of rows to read

#### JSON Extractor (`json_extractor`)

Extracts data from JSON files.

```yaml
extractor:
  plugin: json_extractor
  params:
    path: "data.json"                   # Required: File path
    orient: "records"                   # Optional: JSON orientation
    lines: false                        # Optional: JSON Lines format
    encoding: "utf-8"                   # Optional: File encoding
```

**Parameters**:
- `path` (string, required): Path to JSON file
- `orient` (string): JSON orientation ('records', 'split', 'index', 'columns', 'values')
- `lines` (boolean): Whether file is in JSON Lines format
- `encoding` (string): File encoding (default: 'utf-8')

### Profilers

#### Basic Profiler (`basic_profiler`)

Performs basic data quality analysis.

```yaml
profilers:
  - plugin: basic_profiler
    params:
      check_nulls: true                 # Optional: Check for null values
      check_duplicates: true            # Optional: Check for duplicates
      check_types: true                 # Optional: Check data types
      sample_size: 1000                 # Optional: Sample size for analysis
```

**Parameters**:
- `check_nulls` (boolean): Check for null values (default: true)
- `check_duplicates` (boolean): Check for duplicate rows (default: true)
- `check_types` (boolean): Check data type consistency (default: true)
- `sample_size` (integer): Sample size for analysis (default: 1000)

### Transformers

#### Basic Cleaner (`basic_cleaner`)

Performs basic data cleaning operations.

```yaml
transformers:
  - plugin: basic_cleaner
    params:
      drop_nulls: true                  # Optional: Drop null values
      drop_duplicates: true             # Optional: Remove duplicates
      duplicate_subset: []              # Optional: Columns for duplicate check
      convert_types: {}                 # Optional: Type conversions
      fill_nulls: {}                    # Optional: Fill null values
```

**Parameters**:
- `drop_nulls` (boolean/list): Drop rows with nulls (true=any column, list=specific columns)
- `drop_duplicates` (boolean): Remove duplicate rows
- `duplicate_subset` (list): Columns to consider for duplicate detection
- `convert_types` (dict): Type conversions for columns
- `fill_nulls` (dict): Fill null values with specified values

**Type Conversion Options**:
```yaml
convert_types:
  age: numeric                          # Convert to numeric
  signup_date: datetime                 # Convert to datetime
  category: category                    # Convert to categorical
  status: string                        # Convert to string
```

### Loaders

#### CSV Loader (`csv_loader`)

Writes data to CSV files.

```yaml
loaders:
  - plugin: csv_loader
    params:
      path: "output.csv"                # Required: Output file path
      index: false                      # Optional: Include index
      encoding: "utf-8"                 # Optional: File encoding
      sep: ","                          # Optional: Separator
      na_rep: ""                        # Optional: Null value representation
```

**Parameters**:
- `path` (string, required): Output file path
- `index` (boolean): Include DataFrame index (default: false)
- `encoding` (string): File encoding (default: 'utf-8')
- `sep` (string): Field separator (default: ',')
- `na_rep` (string): Representation for null values

#### JSON Loader (`json_loader`)

Writes data to JSON files.

```yaml
loaders:
  - plugin: json_loader
    params:
      path: "output.json"               # Required: Output file path
      orient: "records"                 # Optional: JSON orientation
      indent: 2                         # Optional: Indentation
      encoding: "utf-8"                 # Optional: File encoding
```

**Parameters**:
- `path` (string, required): Output file path
- `orient` (string): JSON orientation (default: 'records')
- `indent` (integer): Indentation for pretty printing
- `encoding` (string): File encoding (default: 'utf-8')

## 🔧 Environment Variables

### Variable Substitution

Use environment variables in your configuration:

```yaml
extractor:
  plugin: csv_extractor
  params:
    path: "${INPUT_PATH}/data.csv"
    encoding: "${ENCODING:utf-8}"       # Default value if not set
```

### Common Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `INPUT_PATH` | Input data directory | `/data/input` |
| `OUTPUT_PATH` | Output data directory | `/data/output` |
| `DB_CONNECTION` | Database connection string | `postgresql://user:pass@host/db` |
| `API_KEY` | API authentication key | `sk-1234567890abcdef` |
| `ENCODING` | File encoding | `utf-8` |

### Default Values

Use `${VAR:default}` syntax to provide default values:

```yaml
params:
  encoding: "${ENCODING:utf-8}"
  timeout: "${TIMEOUT:300}"
  batch_size: "${BATCH_SIZE:1000}"
```

## 📝 Configuration Examples

### Basic Data Cleaning Pipeline

```yaml
name: "Customer Data Cleaning"
description: "Clean and validate customer data from CSV"

extractor:
  plugin: csv_extractor
  params:
    path: "${INPUT_PATH}/customers.csv"
    header: 0
    encoding: "utf-8"

profilers:
  - plugin: basic_profiler
    params:
      check_nulls: true
      check_duplicates: true
      check_types: true

transformers:
  - plugin: basic_cleaner
    params:
      drop_nulls: ["email", "customer_id"]
      drop_duplicates: true
      duplicate_subset: ["email"]
      convert_types:
        age: numeric
        signup_date: datetime
        status: category

loaders:
  - plugin: csv_loader
    params:
      path: "${OUTPUT_PATH}/cleaned_customers.csv"
      index: false
```

### Multi-Stage Transformation Pipeline

```yaml
name: "Advanced Data Processing"
description: "Multi-stage data transformation with validation"

extractor:
  plugin: csv_extractor
  params:
    path: "${INPUT_PATH}/raw_data.csv"
    header: 0

profilers:
  - plugin: basic_profiler
    params:
      sample_size: 5000

transformers:
  # Stage 1: Basic cleaning
  - plugin: basic_cleaner
    params:
      drop_nulls: ["id", "email"]
      drop_duplicates: true
      convert_types:
        id: numeric
        created_at: datetime

  # Stage 2: Data validation
  - plugin: data_validator
    params:
      rules:
        - column: email
          pattern: "^[^@]+@[^@]+\.[^@]+$"
        - column: age
          type: integer
          min: 0
          max: 120

  # Stage 3: Data enrichment
  - plugin: data_enricher
    params:
      enrichments:
        - column: country_code
          lookup: "${DATA_PATH}/country_codes.csv"
          key_column: "country"
          value_column: "code"

loaders:
  - plugin: csv_loader
    params:
      path: "${OUTPUT_PATH}/processed_data.csv"
  - plugin: json_loader
    params:
      path: "${OUTPUT_PATH}/processed_data.json"
      orient: "records"
```

### Production Pipeline with Error Handling

```yaml
name: "Production Data Pipeline"
description: "Production pipeline with comprehensive error handling"

# Global settings
cache_intermediate_results: true
max_memory_mb: 4000
parallel_execution: true
log_level: "INFO"

extractor:
  plugin: csv_extractor
  params:
    path: "${INPUT_PATH}/production_data.csv"
    encoding: "utf-8"
  on_error: "stop"
  timeout: 600

profilers:
  - plugin: basic_profiler
    params:
      check_nulls: true
      check_duplicates: true
    on_error: "continue"
    timeout: 300

transformers:
  - plugin: basic_cleaner
    params:
      drop_nulls: ["critical_field"]
      drop_duplicates: true
    on_error: "continue"
    timeout: 300

  - plugin: data_validator
    params:
      rules:
        - column: critical_field
          required: true
    on_error: "stop"
    timeout: 300

loaders:
  - plugin: csv_loader
    params:
      path: "${OUTPUT_PATH}/production_output.csv"
    on_error: "stop"
    timeout: 300
```

## ✅ Validation Rules

### Required Fields

- `extractor`: Must be present and valid
- `loaders`: Must be present and contain at least one loader

### Field Validation

| Field | Type | Validation |
|-------|------|------------|
| `name` | string | Non-empty if provided |
| `version` | string | Semantic version format |
| `max_memory_mb` | integer | Must be > 0 |
| `timeout` | integer | Must be > 0 |
| `log_level` | string | Must be valid log level |
| `on_error` | string | Must be valid strategy |

### Plugin Validation

- Plugin name must exist and be available
- Plugin parameters must match plugin schema
- Plugin type must match expected type (extractor, profiler, transformer, loader)

### Environment Variable Validation

- Environment variables must be properly formatted
- Default values must be valid for the parameter type
- Required environment variables must be set

## 🛠️ Configuration Management

### Best Practices

1. **Use Environment Variables**: Keep sensitive data out of configuration files
2. **Version Control**: Store configurations in version control
3. **Environment Separation**: Use different configs for different environments
4. **Documentation**: Add descriptions to explain pipeline purpose
5. **Validation**: Test configurations before deployment

### Configuration Templates

Create reusable configuration templates:

```yaml
# templates/csv-processing.yml
name: "${PIPELINE_NAME}"
description: "${PIPELINE_DESCRIPTION}"

extractor:
  plugin: csv_extractor
  params:
    path: "${INPUT_FILE}"
    encoding: "${ENCODING:utf-8}"

profilers:
  - plugin: basic_profiler
    params: {}

transformers:
  - plugin: basic_cleaner
    params:
      drop_nulls: ${DROP_NULLS:false}
      drop_duplicates: ${DROP_DUPLICATES:true}

loaders:
  - plugin: csv_loader
    params:
      path: "${OUTPUT_FILE}"
```

### Configuration Inheritance

Use base configurations with overrides:

```yaml
# base-config.yml
extractor:
  plugin: csv_extractor
  params:
    encoding: "utf-8"
    header: 0

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
      index: false
```

```yaml
# specific-config.yml
# Inherit from base-config.yml and override specific settings
extractor:
  plugin: csv_extractor
  params:
    path: "specific_data.csv"
    encoding: "utf-8"
    header: 0

transformers:
  - plugin: basic_cleaner
    params:
      drop_duplicates: true
      drop_nulls: ["email"]  # Additional setting
```

## 📚 Additional Resources

- **[Getting Started Guide](getting-started.md)** - Quick start tutorial
- **[User Guide](user-guide.md)** - Comprehensive usage instructions
- **[CLI Reference](cli-reference.md)** - Command-line interface documentation
- **[Plugin Development](plugin-development.md)** - Create custom plugins
- **[Examples](../examples/)** - Sample pipeline configurations

---

**Need help with a specific configuration?** Check out the [User Guide](user-guide.md) for practical examples or the [CLI Reference](cli-reference.md) for validation commands.
