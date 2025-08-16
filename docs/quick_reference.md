# Santiq Quick Reference

A quick reference guide for common Santiq commands and configurations.

## 🚀 Quick Start Commands

```bash
# Install Santiq
pip install santiq

# Check version
santiq version

# Initialize new pipeline
santiq init my-pipeline

# Run pipeline
santiq run pipeline my-pipeline.yml

# List plugins
santiq plugin list
```

## 📋 Pipeline Configuration

### Basic Structure
```yaml
name: "My Pipeline"
extractor:
  plugin: csv_extractor
  params:
    path: "input.csv"
profilers:
  - plugin: basic_profiler
transformers:
  - plugin: basic_cleaner
    params:
      drop_nulls: true
loaders:
  - plugin: csv_loader
    params:
      path: "output.csv"
```

### Environment Variables
```bash
export INPUT_PATH=/path/to/input
export OUTPUT_PATH=/path/to/output
export DB_CONNECTION="postgresql://user:pass@localhost/db"
```

## 🔌 Plugin Management

### List Plugins
```bash
# All plugins
santiq plugin list

# By type
santiq plugin list --type extractor

# External only
santiq plugin list --external
```

### Install Plugins
```bash
# From PyPI
santiq plugin install santiq-plugin-postgres

# Specific version
santiq plugin install santiq-plugin-postgres==1.2.0

# Remove plugin
santiq plugin remove santiq-plugin-postgres
```

### External Plugin Configuration
```bash
# Add configuration
santiq plugin external add my_plugin \
  --package santiq-plugin-my \
  --type transformer

# List configurations
santiq plugin external list

# Remove configuration
santiq plugin external remove my_plugin
```

## ⚙️ Execution Modes

```bash
# Manual - review each fix
santiq run pipeline config.yml --mode manual

# Half-auto - bulk approve/reject
santiq run pipeline config.yml --mode half-auto

# Controlled-auto - auto-apply approved fixes
santiq run pipeline config.yml --mode controlled-auto
```

## 📊 Built-in Plugins

### Extractors
- `csv_extractor` - Read CSV files
- `json_extractor` - Read JSON files
- `excel_extractor` - Read Excel files

### Profilers
- `basic_profiler` - Basic data quality analysis
- `schema_validator` - Validate data schema
- `outlier_detector` - Detect statistical outliers

### Transformers
- `basic_cleaner` - Basic data cleaning
- `data_enricher` - Add calculated columns
- `type_converter` - Convert data types

### Loaders
- `csv_loader` - Write to CSV files
- `json_loader` - Write to JSON files
- `parquet_loader` - Write to Parquet files

## 🔧 Common Parameters

### CSV Extractor
```yaml
extractor:
  plugin: csv_extractor
  params:
    path: "data.csv"
    sep: ";"
    encoding: "utf-8"
    header: 0
    dtype:
      id: "int64"
      price: "float64"
```

### Basic Cleaner
```yaml
transformers:
  - plugin: basic_cleaner
    params:
      drop_nulls: true
      drop_nulls: ["email", "phone"]  # Specific columns
      drop_duplicates: true
      duplicate_subset: ["id"]  # Consider only these columns
      convert_types:
        age: "numeric"
        date: "datetime"
```

### CSV Loader
```yaml
loaders:
  - plugin: csv_loader
    params:
      path: "output.csv"
      sep: ";"
      encoding: "utf-8"
      index: false
      mode: "w"  # w=overwrite, a=append
```

## 🚨 Error Handling

### Plugin Configuration
```yaml
extractor:
  plugin: csv_extractor
  params:
    path: "data.csv"
  on_error: "stop"      # stop, continue, retry
  timeout: 300          # seconds
  enabled: true
```

### Global Settings
```yaml
# Global pipeline settings
cache_intermediate_results: true
max_memory_mb: 2048
temp_dir: "/tmp/santiq"
parallel_execution: true
log_level: "INFO"
```

## 🐛 Troubleshooting

### Common Issues
```bash
# Check plugin availability
santiq plugin list --type extractor

# Verify file paths
ls -la /path/to/your/data

# Enable verbose logging
santiq run pipeline config.yml --verbose

# Check configuration syntax
santiq run pipeline config.yml --dry-run
```

### Debug Mode
```bash
# Set debug logging
export SANTIQ_LOG_LEVEL=DEBUG

# Run with debug output
santiq run pipeline config.yml --verbose
```

## 📁 File Structure

```
my-project/
├── .santiq/
│   └── external_plugins.yml
├── data/
│   ├── input/
│   └── output/
├── pipelines/
│   ├── data-cleaning.yml
│   └── etl-pipeline.yml
└── README.md
```

## 🔗 Useful Links

- [User Guide](user_guide.md) - Comprehensive usage guide
- [Plugin Development](plugin_development.md) - Create custom plugins
- [External Plugin Guide](external_plugin_guide.md) - Manage external plugins
- [Contributing](../CONTRIBUTING.md) - Contribute to Santiq

## 💡 Tips

1. **Start Simple**: Begin with basic ETL, then add complexity
2. **Profile First**: Always profile data before transformation
3. **Use Environment Variables**: Keep configs flexible and secure
4. **Test Incrementally**: Test each component before full pipeline
5. **Monitor Memory**: Set appropriate `max_memory_mb` limits
6. **Enable Caching**: Use `cache_intermediate_results` for complex pipelines
7. **Handle Errors**: Choose appropriate `on_error` strategies
8. **Log Everything**: Enable appropriate log levels for debugging

---

**Need Help?** Check the [User Guide](user_guide.md) or join our community discussions! 🚀
