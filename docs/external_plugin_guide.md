# Santiq External Plugin Management Guide

## Overview

Santiq provides a powerful external plugin management system that allows users to easily discover, install, and manage plugins from PyPI. This system enables the Santiq ecosystem to grow organically while maintaining the stability of the core framework.

## Key Features

- **Automatic Discovery**: Plugins are automatically discovered from PyPI packages
- **Configuration Management**: YAML-based configuration for plugin metadata
- **CLI Integration**: Full command-line interface for plugin management
- **Dependency Resolution**: Automatic handling of plugin dependencies
- **Status Tracking**: Real-time tracking of plugin installation status
- **Lifecycle Management**: Complete plugin lifecycle from installation to removal

## Quick Start

### 1. List Available Plugins

```bash
# List all plugins (built-in, local, and external)
santiq plugin list

# List only external plugins
santiq plugin list --external

# List plugins by type
santiq plugin list --type extractor
```

### 2. Add External Plugin Configuration

```bash
# Add a new external plugin
santiq plugin external add postgres_extractor \
  --package santiq-plugin-postgres-extractor \
  --type extractor \
  --description "Extract data from PostgreSQL databases"
```

### 3. Install External Plugin

```bash
# Install the plugin package
santiq plugin external install postgres_extractor
```

### 4. Use in Pipeline

```yaml
# pipeline.yml
extractor:
  plugin: postgres_extractor
  params:
    host: "localhost"
    database: "mydb"
    query: "SELECT * FROM users"
```

## Configuration Files

### Location

The system automatically looks for configuration files in these locations (in order of precedence):

1. `.santiq/external_plugins.yml` (project-specific)
2. `.santiq/external_plugins.yaml` (project-specific)
3. `~/.santiq/external_plugins.yml` (user-specific)
4. `~/.santiq/external_plugins.yaml` (user-specific)

### Format

```yaml
plugins:
  # Plugin configurations
  postgres_extractor:
    package: "santiq-plugin-postgres-extractor"
    type: "extractor"
    description: "Extract data from PostgreSQL databases"
    version: "1.0.0"
    api_version: "1.0"
    author: "Community Developer"
    license: "MIT"
    homepage: "https://github.com/example/plugin"
    
  json_transformer:
    package: "santiq-plugin-json-transformer"
    type: "transformer"
    description: "Transform data to/from JSON format"
    version: "2.1.0"
    api_version: "1.0"
```

### Required Fields

- `package`: PyPI package name
- `type`: Plugin type (extractor, transformer, profiler, loader)

### Optional Fields

- `description`: Human-readable description
- `version`: Plugin version
- `api_version`: Santiq API compatibility version
- `author`: Plugin author
- `license`: License information
- `homepage`: Plugin homepage URL

## CLI Commands

### Plugin Listing

```bash
# List all plugins
santiq plugin list

# List with filters
santiq plugin list --type extractor --external
santiq plugin list --installed-only
santiq plugin list --available

# Show external plugins only
santiq plugin external list
santiq plugin external list --type extractor
```

### External Plugin Management

```bash
# Add configuration
santiq plugin external add <name> --package <package> --type <type>

# Install package
santiq plugin external install <name>

# Uninstall package
santiq plugin external uninstall <name>

# Remove configuration
santiq plugin external remove <name>
```

### Package Management

```bash
# Install plugin package
santiq plugin install <name>

# Uninstall plugin package
santiq plugin uninstall <name>

# Update plugins
santiq plugin update
santiq plugin update <name>
```

### Information and Search

```bash
# Get plugin information
santiq plugin info <name>

# Search for plugins
santiq plugin search <query>
santiq plugin search <query> --type extractor
```

## Plugin Types

### Extractors

Extractors read data from external sources and return pandas DataFrames.

**Examples:**
- Database connectors (PostgreSQL, MySQL, MongoDB)
- API clients (REST, GraphQL, SOAP)
- File readers (CSV, JSON, Excel, Parquet)
- Cloud storage (S3, GCS, Azure Blob)

### Transformers

Transformers clean, validate, and transform data.

**Examples:**
- Data cleaning (remove duplicates, handle missing values)
- Data validation (check formats, ranges, constraints)
- Data enrichment (add calculated fields, lookups)
- Format conversion (CSV to JSON, XML to DataFrame)

### Profilers

Profilers analyze data quality and detect issues.

**Examples:**
- Data quality assessment
- Anomaly detection
- Statistical analysis
- Schema validation
- Data lineage tracking

### Loaders

Loaders write data to external destinations.

**Examples:**
- Database writers (PostgreSQL, MySQL, MongoDB)
- File writers (CSV, JSON, Parquet, Excel)
- API endpoints (REST, GraphQL)
- Cloud storage (S3, GCS, Azure Blob)

## Plugin Discovery

### How It Works

1. **Configuration Loading**: System loads external plugin configurations
2. **Package Verification**: Checks if PyPI packages are installed
3. **Entry Point Discovery**: Discovers plugins through Python entry points
4. **Registration**: Registers plugins for use in pipelines

### Entry Points

External plugins must register entry points in their `pyproject.toml`:

```toml
[project.entry-points."santiq.extractors"]
postgres_extractor = "my_plugin.extractor:PostgresExtractor"

[project.entry-points."santiq.transformers"]
json_transformer = "my_plugin.transformer:JsonTransformer"
```

### Discovery Order

1. Built-in plugins (core framework)
2. Installed PyPI packages (entry points)
3. External plugin configurations
4. Local plugin directories

## Best Practices

### Plugin Naming

- Use descriptive, lowercase names with underscores
- Follow the pattern: `{source}_{type}` (e.g., `postgres_extractor`)
- Avoid generic names that could conflict

### Version Management

- Use semantic versioning (e.g., `1.0.0`)
- Increment major version for breaking changes
- Test compatibility before major version updates

### Configuration

- Provide comprehensive descriptions
- Include author and license information
- Document required parameters
- Specify API version compatibility

### Dependencies

- Minimize external dependencies
- Use compatible dependency versions
- Document dependency requirements
- Test with different Python versions

## Troubleshooting

### Common Issues

#### Plugin Not Found

```bash
# Check if plugin is configured
santiq plugin external list

# Verify package installation
pip list | grep santiq-plugin

# Check plugin discovery
santiq plugin list --external
```

#### Installation Failures

```bash
# Check internet connectivity
pip install --dry-run package-name

# Verify package exists
pip search package-name

# Check for conflicts
pip check
```

#### Discovery Issues

```bash
# Restart Santiq
# Check entry point configuration
# Verify API version compatibility
```

### Debug Commands

```bash
# Enable debug logging
export SANTIQ_LOG_LEVEL=DEBUG

# Check plugin status
santiq plugin info <name>

# Verify configuration
cat ~/.santiq/external_plugins.yml
```

### Log Files

Check these locations for detailed logs:

- `~/.santiq/logs/` (user logs)
- `.santiq/logs/` (project logs)
- System logs (depending on installation method)

## Examples

### Complete Workflow

```bash
# 1. Add plugin configuration
santiq plugin external add mysql_extractor \
  --package santiq-plugin-mysql-extractor \
  --type extractor \
  --description "Extract data from MySQL databases"

# 2. Install plugin package
santiq plugin external install mysql_extractor

# 3. Verify installation
santiq plugin list --external

# 4. Use in pipeline
santiq run pipeline.yml
```

### Pipeline Configuration

```yaml
# pipeline.yml
name: "Data Pipeline"
version: "1.0.0"

extractor:
  plugin: mysql_extractor
  params:
    host: "localhost"
    port: 3306
    database: "mydb"
    username: "user"
    password: "${DB_PASSWORD}"
    query: "SELECT * FROM users WHERE active = 1"

transformers:
  - plugin: data_cleaner
    params:
      remove_duplicates: true
      handle_missing: "drop"
      
  - plugin: json_transformer
    params:
      output_format: "json"
      validate_schema: true

loaders:
  - plugin: csv_loader
    params:
      path: "output/users.csv"
      index: false
```

### Configuration File Example

```yaml
# ~/.santiq/external_plugins.yml
plugins:
  mysql_extractor:
    package: "santiq-plugin-mysql-extractor"
    type: "extractor"
    description: "Extract data from MySQL databases with connection pooling"
    version: "1.2.0"
    api_version: "1.0"
    author: "Data Team"
    license: "MIT"
    homepage: "https://github.com/example/santiq-plugin-mysql-extractor"
    
  data_cleaner:
    package: "santiq-plugin-data-cleaner"
    type: "transformer"
    description: "Advanced data cleaning and validation"
    version: "2.0.0"
    api_version: "1.0"
    author: "Quality Team"
    license: "Apache-2.0"
    homepage: "https://github.com/example/santiq-plugin-data-cleaner"
```

## Advanced Topics

### Custom Package Indexes

```bash
# Install from custom index
santiq plugin external install <name> --source https://custom.pypi.org/simple/
```

### Plugin Updates

```bash
# Update specific plugin
santiq plugin update <name>

# Update all plugins
santiq plugin update

# Check for updates
santiq plugin list --external
```

### Plugin Dependencies

```bash
# Install with dependencies
pip install santiq-plugin-name[extra]

# Check dependencies
pip show santiq-plugin-name
```

### Environment Variables

```bash
# Custom config directory
export SANTIQ_CONFIG_DIR=/custom/path

# Custom log level
export SANTIQ_LOG_LEVEL=DEBUG

# Custom plugin directory
export SANTIQ_PLUGIN_DIR=/custom/plugins
```

## Support and Community

### Getting Help

- **Documentation**: Check this guide and the main Santiq documentation
- **Issues**: Report bugs and feature requests on GitHub
- **Discussions**: Join community discussions and Q&A
- **Examples**: Browse example plugins and configurations

### Contributing

- **Plugin Development**: Create and share your own plugins
- **Documentation**: Help improve guides and examples
- **Testing**: Test plugins and report compatibility issues
- **Feedback**: Share your experience and suggestions

### Resources

- **Plugin Repository**: Browse available plugins
- **Development Guide**: Learn how to create plugins
- **API Reference**: Complete plugin API documentation
- **Tutorials**: Step-by-step guides and examples

## Conclusion

The Santiq external plugin management system provides a powerful and flexible way to extend the framework's capabilities. By following the guidelines in this guide, you can effectively manage external plugins and build robust data pipelines.

Remember to:
- Use descriptive names and comprehensive descriptions
- Follow versioning and compatibility guidelines
- Test plugins thoroughly before production use
- Keep configurations organized and documented
- Stay updated with the latest plugin versions

Happy plugin management!

