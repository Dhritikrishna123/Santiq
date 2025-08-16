# Santiq User Guide

A comprehensive guide for using Santiq ETL platform for data processing workflows.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Core Concepts](#core-concepts)
3. [Pipeline Configuration](#pipeline-configuration)
4. [Execution Modes](#execution-modes)
5. [Plugin Management](#plugin-management)
6. [CLI Reference](#cli-reference)
7. [Best Practices](#best-practices)
8. [Troubleshooting](#troubleshooting)

## Getting Started

### Installation

```bash
# Install Santiq
pip install santiq

# Verify installation
santiq version
```

### Your First Pipeline

```bash
# Initialize a new pipeline
santiq init my-first-pipeline

# This creates my-first-pipeline.yml
# Edit the file to configure your data sources

# Run the pipeline
santiq run pipeline my-first-pipeline.yml
```

## Core Concepts

### ETL Pipeline Components

Santiq pipelines consist of four main components:

1. **Extractors**: Read data from sources (files, databases, APIs)
2. **Profilers**: Analyze data quality and detect issues
3. **Transformers**: Clean, validate, and transform data
4. **Loaders**: Write data to destinations

### Data Flow

```
Data Source → Extract → Profile → Transform → Load → Destination
```

## Pipeline Configuration

### Basic Pipeline Structure

```yaml
name: "My Data Pipeline"
description: "Process customer data"

extractor:
  plugin: csv_extractor
  params:
    path: "${INPUT_PATH}/customers.csv"
    header: 0

profilers:
  - plugin: basic_profiler
    params: {}

transformers:
  - plugin: basic_cleaner
    params:
      drop_nulls: true
      drop_duplicates: true

loaders:
  - plugin: csv_loader
    params:
      path: "${OUTPUT_PATH}/cleaned_customers.csv"
```

### Environment Variables

Use environment variables for dynamic configuration:

```bash
export INPUT_PATH=/path/to/input/data
export OUTPUT_PATH=/path/to/output
export DB_CONNECTION="postgresql://user:pass@localhost/db"
```

### Advanced Configuration

```yaml
name: "Advanced Pipeline"
version: "2.0.0"

# Global settings
cache_intermediate_results: true
max_memory_mb: 2048
temp_dir: "/tmp/santiq"
parallel_execution: true
log_level: "INFO"

extractor:
  plugin: postgres_extractor
  params:
    connection_string: "${DB_CONNECTION}"
    query: "SELECT * FROM customers WHERE active = true"
  on_error: "retry"
  timeout: 300
  enabled: true

profilers:
  - plugin: basic_profiler
    params: {}
  - plugin: schema_validator
    params:
      expected_schema:
        - name: "customer_id"
          type: "integer"
          required: true

transformers:
  - plugin: basic_cleaner
    params:
      drop_nulls: ["email", "phone"]
      drop_duplicates: true
      duplicate_subset: ["customer_id"]
  - plugin: data_enricher
    params:
      enrich_columns:
        - name: "full_name"
          expression: "CONCAT(first_name, ' ', last_name)"
        - name: "age_group"
          expression: "CASE WHEN age < 30 THEN 'Young' WHEN age < 50 THEN 'Middle' ELSE 'Senior' END"

loaders:
  - plugin: csv_loader
    params:
      path: "${OUTPUT_PATH}/customers_cleaned.csv"
      sep: ";"
      encoding: "utf-8"
  - plugin: postgres_loader
    params:
      connection_string: "${DB_CONNECTION}"
      table: "customers_processed"
      if_exists: "replace"
```

## Execution Modes

### Manual Mode

Review and approve each suggested fix individually:

```bash
santiq run pipeline my-pipeline.yml --mode manual
```

**Use Case**: When you need full control over data transformations

### Half-Auto Mode

Bulk approve/reject fix suggestions:

```bash
santiq run pipeline my-pipeline.yml --mode half-auto
```

**Use Case**: When you want to review fix categories but not individual fixes

### Controlled-Auto Mode

Automatically apply previously approved fix types:

```bash
santiq run pipeline my-pipeline.yml --mode controlled-auto
```

**Use Case**: For production pipelines with known, safe transformations

## Plugin Management

### List Available Plugins

```bash
# List all plugins
santiq plugin list

# List by type
santiq plugin list --type extractor

# List external plugins only
santiq plugin list --external
```

### Install External Plugins

```bash
# Install from PyPI
santiq plugin install santiq-plugin-postgres

# Install with specific version
santiq plugin install santiq-plugin-postgres==1.2.0

# Install from custom index
santiq plugin install santiq-plugin-custom --index-url https://custom.pypi.org/simple/
```

### Manage External Plugin Configuration

```bash
# Add external plugin configuration
santiq plugin external add my_plugin \
  --package santiq-plugin-my \
  --type transformer \
  --description "My custom transformer"

# List external plugin configurations
santiq plugin external list

# Remove external plugin configuration
santiq plugin external remove my_plugin
```

## CLI Reference

### Main Commands

```bash
# Show version
santiq version

# Initialize new pipeline
santiq init <pipeline-name>

# Run pipeline
santiq run pipeline <config-file> [OPTIONS]

# Plugin management
santiq plugin <command> [OPTIONS]

# Show help
santiq --help
santiq run --help
santiq plugin --help
```

### Pipeline Execution Options

```bash
santiq run pipeline config.yml \
  --mode half-auto \
  --plugin-dir ./local-plugins \
  --verbose
```

### Plugin Management Commands

```bash
# List plugins
santiq plugin list [--type TYPE] [--external] [--available]

# Install plugin
santiq plugin install <plugin-name> [--upgrade] [--index-url URL]

# Remove plugin
santiq plugin remove <plugin-name>

# External plugin management
santiq plugin external add <name> [OPTIONS]
santiq plugin external remove <name>
santiq plugin external list
```

## Best Practices

### Pipeline Design

1. **Start Simple**: Begin with basic extract-transform-load, then add complexity
2. **Use Environment Variables**: Keep configuration flexible and secure
3. **Test Incrementally**: Test each component before building the full pipeline
4. **Document Your Workflows**: Add descriptions and version information

### Data Quality

1. **Profile First**: Always profile data before transformation
2. **Validate Assumptions**: Check data types, ranges, and formats
3. **Handle Edge Cases**: Plan for missing data, duplicates, and anomalies
4. **Monitor Results**: Review transformation outputs and adjust as needed

### Performance

1. **Use Appropriate Chunk Sizes**: Balance memory usage with processing speed
2. **Enable Caching**: Use `cache_intermediate_results` for complex pipelines
3. **Parallel Processing**: Enable `parallel_execution` when possible
4. **Memory Management**: Set appropriate `max_memory_mb` limits

### Error Handling

1. **Set Timeouts**: Configure appropriate timeouts for external connections
2. **Use Error Strategies**: Choose between `stop`, `continue`, or `retry`
3. **Log Everything**: Enable appropriate log levels for debugging
4. **Graceful Degradation**: Handle partial failures gracefully

## Troubleshooting

### Common Issues

#### Pipeline Fails to Start

```bash
# Check configuration syntax
santiq run pipeline config.yml --dry-run

# Verify plugin availability
santiq plugin list --type extractor

# Check file permissions and paths
ls -la /path/to/your/data
```

#### Data Extraction Issues

```bash
# Test extractor plugin directly
python -c "
from santiq.plugins.extractors.csv_extractor import CSVExtractor
extractor = CSVExtractor()
extractor.setup({'path': '/path/to/file.csv'})
print(extractor.get_schema_info())
"

# Check file format and encoding
file /path/to/your/data.csv
head -5 /path/to/your/data.csv
```

#### Transformation Problems

```bash
# Enable verbose logging
santiq run pipeline config.yml --verbose

# Check intermediate results
# Look for temp files in configured temp directory
```

#### Plugin Loading Issues

```bash
# Verify plugin installation
pip list | grep santiq

# Check plugin compatibility
santiq plugin list --type extractor

# Reinstall problematic plugins
santiq plugin remove <plugin-name>
santiq plugin install <plugin-name>
```

### Debug Mode

Enable debug logging for detailed troubleshooting:

```bash
# Set debug log level
export SANTIQ_LOG_LEVEL=DEBUG

# Run with debug output
santiq run pipeline config.yml --verbose
```

### Getting Help

1. **Check Documentation**: Review this guide and plugin-specific docs
2. **Review Logs**: Check log files for detailed error information
3. **Community Support**: Join our Discord or GitHub discussions
4. **Issue Reporting**: Report bugs with detailed reproduction steps

## Examples

### Data Cleaning Pipeline

```yaml
name: "Customer Data Cleaning"
description: "Clean and validate customer data from multiple sources"

extractor:
  plugin: csv_extractor
  params:
    path: "${INPUT_PATH}/customers_raw.csv"
    encoding: "latin-1"
    dtype:
      customer_id: "int64"
      age: "int64"

profilers:
  - plugin: basic_profiler
  - plugin: schema_validator
    params:
      expected_schema:
        - name: "customer_id"
          type: "integer"
          required: true
        - name: "email"
          type: "string"
          required: true

transformers:
  - plugin: basic_cleaner
    params:
      drop_nulls: ["customer_id", "email"]
      drop_duplicates: true
      duplicate_subset: ["customer_id"]
      convert_types:
        age: "numeric"
        signup_date: "datetime"
  - plugin: email_validator
    params:
      email_column: "email"
      invalid_action: "nullify"

loaders:
  - plugin: csv_loader
    params:
      path: "${OUTPUT_PATH}/customers_clean.csv"
      index: false
  - plugin: json_loader
    params:
      path: "${OUTPUT_PATH}/customers_clean.json"
      orient: "records"
```

### Database ETL Pipeline

```yaml
name: "Sales Data ETL"
description: "Extract sales data, transform, and load to data warehouse"

extractor:
  plugin: postgres_extractor
  params:
    connection_string: "${DB_CONNECTION}"
    query: |
      SELECT 
        s.sale_id,
        s.sale_date,
        c.customer_name,
        p.product_name,
        s.quantity,
        s.unit_price,
        s.total_amount
      FROM sales s
      JOIN customers c ON s.customer_id = c.customer_id
      JOIN products p ON s.product_id = p.product_id
      WHERE s.sale_date >= CURRENT_DATE - INTERVAL '30 days'
    chunk_size: 10000

profilers:
  - plugin: basic_profiler
  - plugin: outlier_detector
    params:
      columns: ["quantity", "unit_price", "total_amount"]
      method: "iqr"

transformers:
  - plugin: basic_cleaner
    params:
      drop_nulls: ["sale_id", "sale_date"]
      drop_duplicates: true
  - plugin: data_enricher
    params:
      enrich_columns:
        - name: "sale_month"
          expression: "EXTRACT(MONTH FROM sale_date)"
        - name: "sale_year"
          expression: "EXTRACT(YEAR FROM sale_date)"
        - name: "profit_margin"
          expression: "((unit_price - cost_price) / unit_price) * 100"

loaders:
  - plugin: postgres_loader
    params:
      connection_string: "${WAREHOUSE_CONNECTION}"
      table: "sales_fact"
      if_exists: "append"
      chunk_size: 5000
  - plugin: parquet_loader
    params:
      path: "${OUTPUT_PATH}/sales_data.parquet"
      compression: "snappy"
```

## Conclusion

This guide covers the essential aspects of using Santiq for your data processing needs. Remember to:

- Start with simple pipelines and gradually add complexity
- Always profile your data before transformation
- Use appropriate execution modes for your use case
- Leverage the plugin ecosystem for specialized functionality
- Monitor and log your pipeline executions

For more advanced topics, see the [Plugin Development Guide](plugin_development.md) and [External Plugin Guide](external_plugin_guide.md).

Happy data processing! 🚀
