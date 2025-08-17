# CLI Reference

Complete reference for Santiq command-line interface commands, options, and usage examples.

## 📋 Table of Contents

1. [Overview](#overview)
2. [Global Commands](#global-commands)
3. [Pipeline Commands](#pipeline-commands)
4. [Plugin Commands](#plugin-commands)
5. [Command Options](#command-options)
6. [Examples](#examples)
7. [Exit Codes](#exit-codes)

## 🎯 Overview

Santiq provides a comprehensive command-line interface for managing pipelines, plugins, and data processing workflows.

### Basic Usage

```bash
santiq [COMMAND] [OPTIONS] [ARGUMENTS]
```

### Getting Help

```bash
# Show general help
santiq --help

# Show help for specific command
santiq run --help
santiq plugin --help

# Show help for subcommand
santiq plugin list --help
```

## 🌐 Global Commands

### Version

Display Santiq version information.

```bash
santiq --version
```

**Output**:
```
santiq version 0.1.0
```

### Init

Initialize a new pipeline configuration file.

```bash
santiq init [PIPELINE_NAME] [OPTIONS]
```

**Arguments**:
- `PIPELINE_NAME` (required): Name of the pipeline

**Options**:
- `--template, -t`: Template to use (default: "basic")

**Examples**:
```bash
# Create basic pipeline
santiq init my-pipeline

# Create pipeline with specific template
santiq init my-pipeline --template advanced
```

**Output**:
```
✓ Created pipeline config: my-pipeline.yml
Tip: Set INPUT_PATH and OUTPUT_PATH environment variables
```

## 🚀 Pipeline Commands

### Run Pipeline

Execute a pipeline from configuration file.

```bash
santiq run pipeline [CONFIG_FILE] [OPTIONS]
```

**Arguments**:
- `CONFIG_FILE` (required): Path to pipeline configuration file

**Options**:
- `--mode, -m`: Execution mode (manual, half-auto, controlled-auto) [default: manual]
- `--plugin-dir, -d`: Additional plugin directory
- `--verbose, -v`: Verbose output
- `--dry-run`: Test configuration without execution

**Examples**:
```bash
# Run pipeline in manual mode
santiq run pipeline config.yml --mode manual

# Run pipeline with verbose output
santiq run pipeline config.yml --verbose

# Test configuration without execution
santiq run pipeline config.yml --dry-run

# Run with custom plugin directory
santiq run pipeline config.yml --plugin-dir ./plugins
```

**Output**:
```
Starting pipeline: config.yml
Mode: manual
✓ Pipeline completed successfully

┌─────────────────┬─────────────────┐
│ Metric          │ Value           │
├─────────────────┼─────────────────┤
│ Pipeline ID     │ abc123def456    │
│ Rows Processed  │ 1000            │
│ Fixes Applied   │ 5               │
└─────────────────┴─────────────────┘
```

### History

View pipeline execution history.

```bash
santiq run history [OPTIONS]
```

**Options**:
- `--pipeline-id, -p`: Specific pipeline ID
- `--limit, -l`: Number of recent executions to show [default: 10]

**Examples**:
```bash
# Show recent executions
santiq run history

# Show specific pipeline history
santiq run history --pipeline-id abc123def456

# Show more history entries
santiq run history --limit 50
```

**Output**:
```
Recent pipeline executions: (last 10)

┌──────────────┬─────────────────────┬──────────────┬────────┐
│ Pipeline ID  │ Timestamp           │ Event        │ Status │
├──────────────┼─────────────────────┼──────────────┼────────┤
│ abc123de...  │ 2024-01-15 10:30:15 │ pipeline_sta │ ✓      │
│ def456gh...  │ 2024-01-15 09:15:22 │ pipeline_sta │ ✓      │
│ ghi789ij...  │ 2024-01-14 16:45:33 │ pipeline_sta │ ✗      │
└──────────────┴─────────────────────┴──────────────┴────────┘
```

## 🔌 Plugin Commands

### List Plugins

List installed and available plugins.

```bash
santiq plugin list [OPTIONS]
```

**Options**:
- `--type, -t`: Filter by plugin type (extractor, profiler, transformer, loader)
- `--local-dir, -d`: Include local plugin directory
- `--installed-only`: Show only installed plugins
- `--available`: Show available plugins from registry
- `--external`: Show only external plugins

**Examples**:
```bash
# List all plugins
santiq plugin list

# List extractors only
santiq plugin list --type extractor

# List with local plugins
santiq plugin list --local-dir ./plugins

# Show available plugins
santiq plugin list --available
```

**Output**:
```
Extractors:
┌──────────────┬─────────┬─────┬────────┬────────┬─────────────────────────────┐
│ Name         │ Version │ API │ Source │ Status │ Description                 │
├──────────────┼─────────┼─────┼────────┼────────┼─────────────────────────────┤
│ csv_extractor│ 0.1.0   │ 1.0 │ entry_ │ ✓ Avai │ Extracts data from CSV fi  │
│ json_extract │ 0.1.0   │ 1.0 │ entry_ │ ✓ Avai │ Extracts data from JSON f  │
└──────────────┴─────────┴─────┴────────┴────────┴─────────────────────────────┘
```

### Install Plugin

Install a plugin package.

```bash
santiq plugin install [PLUGIN_NAME] [OPTIONS]
```

**Arguments**:
- `PLUGIN_NAME` (required): Plugin name or package name

**Options**:
- `--source, -s`: Custom package index URL
- `--upgrade, -u`: Upgrade if already installed
- `--pre`: Include pre-release versions
- `--force`: Force reinstall
- `--dry-run`: Show what would be installed

**Examples**:
```bash
# Install plugin
santiq plugin install santiq-plugin-postgres

# Install specific version
santiq plugin install santiq-plugin-postgres==1.2.0

# Install from custom source
santiq plugin install my-plugin --source https://custom.pypi.org/simple/

# Upgrade existing plugin
santiq plugin install santiq-plugin-postgres --upgrade
```

**Output**:
```
Installing official plugin: postgres_extractor (santiq-plugin-postgres)
✓ Successfully installed: santiq-plugin-postgres
Description: Extract data from PostgreSQL databases
✓ Plugin discovery working (5 plugins found)
```

### Uninstall Plugin

Uninstall a plugin package.

```bash
santiq plugin uninstall [PLUGIN_NAME] [OPTIONS]
```

**Arguments**:
- `PLUGIN_NAME` (required): Plugin name or package name

**Options**:
- `--yes, -y`: Skip confirmation
- `--dry-run`: Show what would be uninstalled

**Examples**:
```bash
# Uninstall plugin
santiq plugin uninstall santiq-plugin-postgres

# Uninstall without confirmation
santiq plugin uninstall santiq-plugin-postgres --yes
```

**Output**:
```
Uninstalling: santiq-plugin-postgres
✓ Successfully uninstalled: santiq-plugin-postgres
Successfully uninstalled santiq-plugin-postgres-1.2.0
```

### Search Plugins

Search for available plugins.

```bash
santiq plugin search [QUERY] [OPTIONS]
```

**Arguments**:
- `QUERY` (required): Search term

**Options**:
- `--type, -t`: Filter by plugin type
- `--official-only`: Search only official plugins

**Examples**:
```bash
# Search for database plugins
santiq plugin search database

# Search for extractors only
santiq plugin search csv --type extractor

# Search official plugins only
santiq plugin search postgres --official-only
```

**Output**:
```
Searching for: 'database'

┌──────────────┬─────────────────────┬──────────────┬────────┬─────────────────────────────┐
│ Name         │ Package             │ Categories   │ Status │ Description                 │
├──────────────┼─────────────────────┼──────────────┼────────┼─────────────────────────────┤
│ postgres_ext │ santiq-plugin-postg │ extractor    │ Offici │ Extract data from PostgreS  │
│ mysql_extrac │ santiq-plugin-mysql │ extractor    │ Offici │ Extract data from MySQL da  │
└──────────────┴─────────────────────┴──────────────┴────────┴─────────────────────────────┘

Found 2 plugin(s)
```

### Plugin Info

Show detailed information about a plugin.

```bash
santiq plugin info [PLUGIN_NAME] [OPTIONS]
```

**Arguments**:
- `PLUGIN_NAME` (required): Name of the plugin

**Options**:
- `--type, -t`: Plugin type (if multiple types exist)
- `--local-dir, -d`: Include local plugin directory

**Examples**:
```bash
# Show plugin info
santiq plugin info csv_extractor

# Show info with local plugins
santiq plugin info my_plugin --local-dir ./plugins
```

**Output**:
```
Registry Information: csv_extractor
Package: santiq-plugin-csv-extractor
Categories: extractor
Status: Official
Description: Extract data from CSV files

Installed Plugin Information: csv_extractor
Name: CSV Extractor
Type: extractor
Version: 0.1.0
API Version: 1.0
Source: entry_point
Description: Extracts data from CSV files with configurable options
```

### Update Plugins

Update installed plugins.

```bash
santiq plugin update [OPTIONS]
```

**Options**:
- `PLUGIN_NAME`: Update specific plugin (otherwise update all)
- `--dry-run`: Show what would be updated
- `--pre`: Include pre-release versions

**Examples**:
```bash
# Update all plugins
santiq plugin update

# Update specific plugin
santiq plugin update santiq-plugin-postgres

# Show what would be updated
santiq plugin update --dry-run
```

**Output**:
```
Found 3 Santiq plugin(s) to update:
  • santiq-plugin-postgres
  • santiq-plugin-mysql
  • santiq-plugin-elasticsearch

Updating: santiq-plugin-postgres
✓ Updated: santiq-plugin-postgres
```

### External Plugin Management

Manage external plugin configurations.

```bash
santiq plugin external [ACTION] [PLUGIN_NAME] [OPTIONS]
```

**Actions**:
- `add`: Add external plugin configuration
- `remove`: Remove external plugin configuration
- `list`: List external plugins
- `install`: Install external plugin package
- `uninstall`: Uninstall external plugin package

**Options for `add`**:
- `--package, -p`: PyPI package name (required)
- `--type, -t`: Plugin type (required)
- `--description, -d`: Plugin description
- `--version, -v`: Plugin version
- `--api-version, -a`: API version

**Examples**:
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

**Output**:
```
✓ Added external plugin configuration: postgres_extractor
Package: santiq-plugin-postgres
Type: extractor
⚠ Package not installed - use 'santiq plugin external install' to install
```

## ⚙️ Command Options

### Global Options

| Option | Description | Example |
|--------|-------------|---------|
| `--help, -h` | Show help message | `santiq --help` |
| `--version, -V` | Show version | `santiq --version` |

### Verbose Output

Use `--verbose` or `-v` to get detailed output:

```bash
santiq run pipeline config.yml --verbose
```

**Output**:
```
Starting pipeline: config.yml
Mode: manual
Plugin directory: None
Loading configuration...
Configuration loaded successfully
Initializing plugins...
Plugin csv_extractor initialized
Plugin basic_profiler initialized
Plugin basic_cleaner initialized
Plugin csv_loader initialized
Running pipeline...
Extracting data...
Profiling data...
Transforming data...
Loading data...
✓ Pipeline completed successfully
```

### Dry Run

Use `--dry-run` to test configurations without execution:

```bash
santiq run pipeline config.yml --dry-run
```

**Output**:
```
Configuration validation: ✓ PASSED
Plugin discovery: ✓ PASSED
Environment variables: ✓ PASSED
File permissions: ✓ PASSED
Configuration is valid and ready to run
```

## 📝 Examples

### Complete Workflow Example

```bash
# 1. Initialize a new pipeline
santiq init customer-cleanup

# 2. Edit the configuration file
# customer-cleanup.yml

# 3. Install required plugins
santiq plugin install santiq-plugin-postgres

# 4. List available plugins
santiq plugin list

# 5. Run the pipeline
santiq run pipeline customer-cleanup.yml --mode manual

# 6. Check pipeline history
santiq run history

# 7. Get plugin information
santiq plugin info csv_extractor
```

### Advanced Plugin Management

```bash
# Add external plugin configuration
santiq plugin external add elasticsearch_loader \
  --package santiq-plugin-elasticsearch \
  --type loader \
  --description "Load data to Elasticsearch"

# Install the plugin
santiq plugin external install elasticsearch_loader

# Verify installation
santiq plugin list --type loader

# Update plugins
santiq plugin update

# Search for new plugins
santiq plugin search "machine learning"
```

### Production Pipeline Execution

```bash
# Run with controlled-auto mode for production
santiq run pipeline production.yml --mode controlled-auto

# Run with custom plugin directory
santiq run pipeline production.yml \
  --plugin-dir /opt/santiq/plugins \
  --mode controlled-auto

# Check execution history
santiq run history --limit 20

# Get specific pipeline details
santiq run history --pipeline-id abc123def456
```

### Troubleshooting Commands

```bash
# Validate configuration
santiq run pipeline config.yml --dry-run

# Check plugin availability
santiq plugin list --verbose

# Search for missing plugins
santiq plugin search "database"

# Get detailed plugin information
santiq plugin info missing_plugin

# Check pipeline history for errors
santiq run history --limit 50
```

## 🔢 Exit Codes

Santiq uses standard exit codes to indicate command success or failure:

| Exit Code | Description |
|-----------|-------------|
| `0` | Success |
| `1` | General error |
| `2` | Configuration error |
| `3` | Plugin error |
| `4` | Pipeline execution error |
| `5` | File/permission error |

### Error Handling

```bash
# Check exit code
santiq run pipeline config.yml
echo $?  # Should be 0 for success

# Handle errors in scripts
if santiq run pipeline config.yml; then
    echo "Pipeline completed successfully"
else
    echo "Pipeline failed with exit code $?"
    exit 1
fi
```

## 🛠️ Tips and Best Practices

### Command Aliases

Create useful aliases in your shell configuration:

```bash
# Add to ~/.bashrc or ~/.zshrc
alias santiq-run='santiq run pipeline'
alias santiq-list='santiq plugin list'
alias santiq-install='santiq plugin install'
alias santiq-history='santiq run history'
```

### Environment Variables

Set common environment variables:

```bash
# Add to ~/.bashrc or ~/.zshrc
export SANTIQ_INPUT_PATH="/data/input"
export SANTIQ_OUTPUT_PATH="/data/output"
export SANTIQ_PLUGIN_DIR="/opt/santiq/plugins"
```

### Scripting Examples

```bash
#!/bin/bash
# Run multiple pipelines

PIPELINES=("pipeline1.yml" "pipeline2.yml" "pipeline3.yml")

for pipeline in "${PIPELINES[@]}"; do
    echo "Running $pipeline..."
    if santiq run pipeline "$pipeline" --mode controlled-auto; then
        echo "✓ $pipeline completed successfully"
    else
        echo "✗ $pipeline failed"
        exit 1
    fi
done
```

## 📚 Additional Resources

- **[Getting Started Guide](getting-started.md)** - Quick start tutorial
- **[User Guide](user-guide.md)** - Comprehensive usage instructions
- **[Configuration Reference](configuration.md)** - Configuration options
- **[Plugin Development](plugin-development.md)** - Create custom plugins
- **[Examples](../examples/)** - Sample pipelines and configurations

---

**Need help with a specific command?** Check out the [User Guide](user-guide.md) for practical examples or the [Configuration Reference](configuration.md) for configuration options.
