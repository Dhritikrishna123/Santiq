# Santiq User Guide

A comprehensive guide to using Santiq for data processing workflows. This guide covers everything from basic usage to advanced features and best practices.

## 📋 Table of Contents

1. [Overview](#overview)
2. [Pipeline Configuration](#pipeline-configuration)
3. [Plugin Management](#plugin-management)
4. [Execution Modes](#execution-modes)
5. [Advanced Features](#advanced-features)
6. [Best Practices](#best-practices)
7. [Troubleshooting](#troubleshooting)

## 🎯 Overview

Santiq is a plugin-first ETL platform that makes data processing simple, reliable, and extensible. This guide will help you master all aspects of using Santiq effectively.

### Key Concepts

- **ETL Pipeline**: Extract data from sources, transform it, and load it to destinations
- **Plugin Architecture**: Every component is a plugin that can be mixed and matched
- **Execution Modes**: Choose how much automation you want in your data processing
- **Audit Trail**: Every operation is logged for transparency and debugging

## ⚙️ Pipeline Configuration

### Basic Pipeline Structure

Every Santiq pipeline consists of four main sections:

```yaml
name: "My Pipeline"
description: "Description of what this pipeline does"

extractor:
  plugin: csv_extractor
  params:
    path: "input.csv"

profilers:
  - plugin: basic_profiler
    params: {}

transformers:
  - plugin: basic_cleaner
    params:
      drop_nulls: true

loaders:
  - plugin: csv_loader
    params:
      path: "output.csv"
```

### Configuration Options

#### Global Settings

```yaml
# Global pipeline settings
cache_intermediate_results: true
max_memory_mb: 1000
temp_dir: "/tmp/santiq"
parallel_execution: false
log_level: "INFO"
```

#### Plugin Configuration

Each plugin can be configured with:

```yaml
plugin: plugin_name
params:
  # Plugin-specific parameters
  param1: value1
  param2: value2
on_error: "stop"  # stop, continue, retry
enabled: true
timeout: 300  # seconds
```

### Environment Variable Substitution

Use environment variables for dynamic configuration:

```yaml
extractor:
  plugin: csv_extractor
  params:
    path: "${INPUT_PATH}/data.csv"
    encoding: "${ENCODING:utf-8}"  # Default value if not set
```

### Advanced Configuration Examples

#### Multiple Transformers

```yaml
transformers:
  - plugin: basic_cleaner
    params:
      drop_nulls: true
      drop_duplicates: true
  
  - plugin: data_validator
    params:
      rules:
        - column: email
          pattern: "^[^@]+@[^@]+\.[^@]+$"
  
  - plugin: data_enricher
    params:
      enrichments:
        - column: country
          lookup: "country_codes.csv"
```

#### Conditional Processing

```yaml
transformers:
  - plugin: conditional_cleaner
    params:
      conditions:
        - when: "column_value > 100"
          action: "drop_row"
        - when: "is_null(column)"
          action: "fill_default"
          default_value: "unknown"
```

## 🔌 Plugin Management

### Built-in Plugins

Santiq comes with several built-in plugins:

#### Extractors
- `csv_extractor`: Read CSV files
- `json_extractor`: Read JSON files
- `excel_extractor`: Read Excel files

#### Profilers
- `basic_profiler`: Basic data quality analysis

#### Transformers
- `basic_cleaner`: Basic data cleaning operations

#### Loaders
- `csv_loader`: Write to CSV files
- `excel_loader`: Write to Excel files
- `json_loader`: Write to JSON files

### Installing Community Plugins

```bash
# Install from PyPI
santiq plugin install santiq-plugin-postgres

# Install specific version
santiq plugin install santiq-plugin-postgres==1.2.0

# Install from custom index
santiq plugin install my-plugin --source https://custom.pypi.org/simple/
```

### Managing External Plugins

```bash
# Add external plugin configuration
santiq plugin external add postgres_extractor \
  --package santiq-plugin-postgres \
  --type extractor \
  --description "PostgreSQL data extractor"

# List external plugins
santiq plugin external list

# Install external plugin
santiq plugin external install postgres_extractor

# Remove external plugin
santiq plugin external remove postgres_extractor
```

### Plugin Discovery

```bash
# List all plugins
santiq plugin list

# List by type
santiq plugin list --type extractor

# Show only external plugins
santiq plugin list --external

# Show only installed plugins
santiq plugin list --installed-only
```

### Plugin Information

```bash
# Get detailed plugin info
santiq plugin info csv_extractor

# Search for plugins
santiq plugin search "database"

# Update plugins
santiq plugin update
santiq plugin update csv_extractor
```

## 🔄 Execution Modes

Santiq offers three execution modes to fit different workflows:

### Manual Mode

**Use when**: Learning, debugging, or processing critical data

```bash
santiq run pipeline config.yml --mode manual
```

**Behavior**:
- Review each suggested fix before applying
- Full control over data changes
- Interactive prompts for decisions

**Example output**:
```
Found 5 data quality issues:
1. 2 rows with null values in email column
2. 1 duplicate row detected
3. Age column contains non-numeric values

Apply fix for null values in email? (y/n): y
Apply fix for duplicate rows? (y/n): n
Apply fix for age column? (y/n): y
```

### Half-Auto Mode

**Use when**: Regular data processing with oversight

```bash
santiq run pipeline config.yml --mode half-auto
```

**Behavior**:
- Bulk approve/reject fix types
- Preferences saved for future runs
- Efficient processing with oversight

**Example output**:
```
Found 3 fix types:
1. drop_nulls (2 rows affected)
2. drop_duplicates (1 row affected)
3. convert_types (1 column affected)

Approve all fixes of type 'drop_nulls'? (y/n): y
Approve all fixes of type 'drop_duplicates'? (y/n): y
Approve all fixes of type 'convert_types'? (y/n): n
```

### Controlled-Auto Mode

**Use when**: Production, trusted pipelines

```bash
santiq run pipeline config.yml --mode controlled-auto
```

**Behavior**:
- Automatically apply previously approved fix types
- No user interaction required
- Fastest execution

**Example output**:
```
Running in controlled-auto mode
Applying previously approved fixes:
- drop_nulls: 2 rows affected
- drop_duplicates: 1 row affected
Pipeline completed successfully
```

## 🚀 Advanced Features

### Pipeline History and Auditing

```bash
# View recent pipeline executions
santiq run history

# View history for specific pipeline
santiq run history --pipeline-id abc123def456

# View detailed audit log
santiq run history --limit 50
```

### Environment-Specific Configurations

Create different configuration files for different environments:

```bash
# Development
santiq run pipeline config-dev.yml

# Staging
santiq run pipeline config-staging.yml

# Production
santiq run pipeline config-prod.yml
```

### Parallel Processing

Enable parallel execution for better performance:

```yaml
# Global settings
parallel_execution: true

# Plugin-specific settings
transformers:
  - plugin: basic_cleaner
    params:
      parallel: true
      workers: 4
```

### Memory Management

Control memory usage for large datasets:

```yaml
# Global memory limit
max_memory_mb: 2000

# Cache intermediate results
cache_intermediate_results: true

# Temporary directory for large files
temp_dir: "/tmp/santiq"
```

### Error Handling

Configure how plugins handle errors:

```yaml
extractors:
  - plugin: csv_extractor
    params:
      path: "data.csv"
    on_error: "stop"  # stop, continue, retry
    timeout: 300

transformers:
  - plugin: basic_cleaner
    params:
      drop_nulls: true
    on_error: "continue"  # Continue with other transformers
```

### Data Validation

Add validation rules to your pipeline:

```yaml
transformers:
  - plugin: data_validator
    params:
      rules:
        - column: email
          required: true
          pattern: "^[^@]+@[^@]+\.[^@]+$"
        - column: age
          type: "integer"
          min: 0
          max: 120
        - column: status
          allowed_values: ["active", "inactive", "pending"]
```

## 📊 Best Practices

### Pipeline Design

1. **Start Simple**: Begin with basic pipelines and add complexity gradually
2. **Use Descriptive Names**: Name your pipelines and plugins clearly
3. **Document Your Configurations**: Add descriptions to explain what each pipeline does
4. **Test Incrementally**: Test each component before combining them

### Configuration Management

1. **Use Environment Variables**: Keep sensitive data out of configuration files
2. **Version Control**: Store configurations in version control
3. **Environment Separation**: Use different configs for dev/staging/prod
4. **Backup Configurations**: Keep backups of important pipeline configurations

### Performance Optimization

1. **Choose Appropriate Execution Mode**: Use controlled-auto for production
2. **Enable Parallel Processing**: For large datasets
3. **Monitor Memory Usage**: Set appropriate memory limits
4. **Use Efficient Plugins**: Choose plugins optimized for your data size

### Error Handling

1. **Configure Error Strategies**: Use appropriate `on_error` settings
2. **Monitor Audit Logs**: Regularly check pipeline execution history
3. **Set Timeouts**: Prevent hanging operations
4. **Test Error Scenarios**: Verify error handling works as expected

### Data Quality

1. **Profile Your Data**: Always include profiling in your pipelines
2. **Validate Input**: Add validation rules for critical data
3. **Monitor Quality Metrics**: Track data quality over time
4. **Document Data Issues**: Keep records of common data problems

## 🛠️ Troubleshooting

### Common Issues and Solutions

#### Plugin Not Found

**Error**: `Plugin 'unknown_plugin' not found`

**Solution**:
```bash
# Check available plugins
santiq plugin list

# Install missing plugin
santiq plugin install plugin_name

# Check plugin configuration
santiq plugin info plugin_name
```

#### Configuration Errors

**Error**: `Configuration validation failed`

**Solution**:
```bash
# Validate configuration
santiq run pipeline config.yml --dry-run

# Check YAML syntax
python -c "import yaml; yaml.safe_load(open('config.yml'))"
```

#### Memory Issues

**Error**: `Memory limit exceeded`

**Solution**:
```yaml
# Increase memory limit
max_memory_mb: 4000

# Disable caching for large datasets
cache_intermediate_results: false

# Use temporary directory
temp_dir: "/tmp/santiq"
```

#### File Permission Errors

**Error**: `Permission denied`

**Solution**:
```bash
# Check file permissions
ls -la input_file.csv

# Set appropriate permissions
chmod 644 input_file.csv

# Check directory permissions
ls -la output_directory/
```

#### Database Connection Issues

**Error**: `Connection failed`

**Solution**:
```bash
# Check connection string
echo $DB_CONNECTION

# Test connection manually
python -c "import psycopg2; psycopg2.connect('$DB_CONNECTION')"

# Check network connectivity
ping database_host
```

### Debugging Techniques

#### Verbose Output

```bash
# Enable verbose logging
santiq run pipeline config.yml --verbose

# Check specific plugin
santiq plugin info plugin_name --verbose
```

#### Dry Run

```bash
# Test configuration without execution
santiq run pipeline config.yml --dry-run
```

#### Audit Log Analysis

```bash
# View recent audit events
santiq run history --limit 100

# Filter by pipeline ID
santiq run history --pipeline-id abc123def456
```

### Getting Help

```bash
# Show help for any command
santiq --help
santiq run --help
santiq plugin --help

# Show plugin-specific help
santiq plugin info plugin_name
```

## 📚 Additional Resources

- **[Getting Started Guide](getting-started.md)** - Quick start tutorial
- **[Configuration Reference](configuration.md)** - Complete configuration options
- **[CLI Reference](cli-reference.md)** - Command-line interface documentation
- **[Plugin Development](plugin-development.md)** - Create custom plugins
- **[API Reference](api-reference.md)** - Core API documentation
- **[Examples](../examples/)** - Sample pipelines and configurations

---

**Need more help?** Check out the [Configuration Reference](configuration.md) for detailed configuration options or the [CLI Reference](cli-reference.md) for complete command documentation.
