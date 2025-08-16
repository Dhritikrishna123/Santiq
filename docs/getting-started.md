# Getting Started with Santiq

Welcome to Santiq! This guide will help you get up and running with your first data pipeline in minutes.

## 📋 Table of Contents

1. [Installation](#installation)
2. [Core Concepts](#core-concepts)
3. [Your First Pipeline](#your-first-pipeline)
4. [Understanding Execution Modes](#understanding-execution-modes)
5. [Next Steps](#next-steps)

## 🚀 Installation

### Prerequisites

- **Python 3.11 or higher**
- **pip** (Python package installer)

### Install Santiq

```bash
# Install the latest version
pip install santiq

# Verify installation
santiq version
```

You should see output like:
```
santiq version 0.1.0
```

### Optional: Install with Development Dependencies

If you plan to develop plugins or contribute to Santiq:

```bash
pip install santiq[dev]
```

## 🧠 Core Concepts

Santiq follows the ETL (Extract, Transform, Load) pattern with a plugin-first architecture:

### ETL Pipeline Components

1. **Extractors** - Read data from sources (files, databases, APIs)
2. **Profilers** - Analyze data quality and detect issues
3. **Transformers** - Clean, validate, and transform data
4. **Loaders** - Write data to destinations

### Data Flow

```
Data Source → Extract → Profile → Transform → Load → Destination
```

### Plugin Architecture

Everything in Santiq is a plugin, which means:
- **Modular**: Mix and match components as needed
- **Extensible**: Create custom plugins for any data source
- **Maintainable**: Update individual components without affecting others

## 🎯 Your First Pipeline

Let's create a simple pipeline that cleans customer data from a CSV file.

### Step 1: Initialize a Pipeline

```bash
# Create a new pipeline configuration
santiq init customer-cleanup
```

This creates a file called `customer-cleanup.yml` with a basic template.

### Step 2: Prepare Your Data

Create a sample CSV file called `customers.csv`:

```csv
customer_id,name,email,age,signup_date
1,John Doe,john@example.com,25,2023-01-15
2,Jane Smith,jane@example.com,30,2023-02-20
3,Bob Johnson,,35,2023-03-10
4,Alice Brown,alice@example.com,,2023-04-05
5,John Doe,john@example.com,25,2023-01-15
```

### Step 3: Configure Your Pipeline

Edit `customer-cleanup.yml`:

```yaml
name: "Customer Data Cleanup"
description: "Clean and validate customer data from CSV"

extractor:
  plugin: csv_extractor
  params:
    path: "customers.csv"
    header: 0

profilers:
  - plugin: basic_profiler
    params: {}

transformers:
  - plugin: basic_cleaner
    params:
      drop_nulls: ["email"]  # Remove rows with missing emails
      drop_duplicates: true  # Remove duplicate rows
      convert_types:
        age: numeric
        signup_date: datetime

loaders:
  - plugin: csv_loader
    params:
      path: "cleaned_customers.csv"
      index: false
```

### Step 4: Run Your Pipeline

```bash
# Run in manual mode to see what's happening
santiq run pipeline customer-cleanup.yml --mode manual
```

### Step 5: Check Results

After running, you should see:
- A new file `cleaned_customers.csv` with cleaned data
- Console output showing what was processed
- Information about any issues found and fixes applied

## 🔄 Understanding Execution Modes

Santiq offers three execution modes to fit different workflows:

### Manual Mode (`--mode manual`)
- **Best for**: Learning, debugging, critical data
- **Behavior**: Review each suggested fix before applying
- **Use case**: When you want full control over data changes

```bash
santiq run pipeline config.yml --mode manual
```

### Half-Auto Mode (`--mode half-auto`)
- **Best for**: Regular data processing with oversight
- **Behavior**: Bulk approve/reject fix types, preferences saved
- **Use case**: When you want efficiency with some oversight

```bash
santiq run pipeline config.yml --mode half-auto
```

### Controlled-Auto Mode (`--mode controlled-auto`)
- **Best for**: Production, trusted pipelines
- **Behavior**: Automatically apply previously approved fix types
- **Use case**: When you have confidence in your pipeline

```bash
santiq run pipeline config.yml --mode controlled-auto
```

## 🔧 Environment Variables

Use environment variables for dynamic configuration:

```bash
# Set input and output paths
export INPUT_PATH=/path/to/input/data
export OUTPUT_PATH=/path/to/output

# Set database connections
export DB_CONNECTION="postgresql://user:pass@localhost/db"

# Run pipeline (config will use these variables)
santiq run pipeline config.yml
```

In your configuration file, reference them like this:

```yaml
extractor:
  plugin: csv_extractor
  params:
    path: "${INPUT_PATH}/data.csv"

loaders:
  - plugin: csv_loader
    params:
      path: "${OUTPUT_PATH}/result.csv"
```

## 📊 Understanding Pipeline Output

When you run a pipeline, Santiq provides detailed feedback:

```
✓ Pipeline completed successfully

┌─────────────────┬─────────────────┐
│ Metric          │ Value           │
├─────────────────┼─────────────────┤
│ Pipeline ID     │ abc123def456    │
│ Rows Processed  │ 1000            │
│ Fixes Applied   │ 5               │
└─────────────────┴─────────────────┘

Applied Fixes:
  • Dropped 2 rows with null values in email column
  • Removed 1 duplicate row
  • Converted age column to numeric type
  • Converted signup_date column to datetime type
```

## 🛠️ Troubleshooting

### Common Issues

**"Plugin not found" error**
```bash
# List available plugins
santiq plugin list

# Install missing plugins
santiq plugin install <plugin-name>
```

**"File not found" error**
- Check file paths in your configuration
- Ensure environment variables are set correctly
- Verify file permissions

**"Permission denied" error**
- Check file and directory permissions
- Ensure you have write access to output directories

### Getting Help

```bash
# Show help for any command
santiq --help
santiq run --help
santiq plugin --help

# Check pipeline configuration
santiq run pipeline config.yml --dry-run
```

## 🚀 Next Steps

Now that you've created your first pipeline, here's what to explore next:

### 1. Explore Built-in Plugins
```bash
# See what plugins are available
santiq plugin list

# Get detailed info about a plugin
santiq plugin info csv_extractor
```

### 2. Try Different Data Sources
- **JSON files**: Use `json_extractor` plugin
- **Excel files**: Use `excel_extractor` plugin
- **Databases**: Install database plugins

### 3. Advanced Configuration
- **Multiple transformers**: Chain different cleaning operations
- **Conditional processing**: Use different paths based on data conditions
- **Error handling**: Configure how to handle failures

### 4. Create Custom Plugins
- **Simple plugins**: Start with basic data transformations
- **Complex plugins**: Build plugins for specific business logic
- **Share plugins**: Contribute to the community

### 5. Production Deployment
- **Configuration management**: Use environment-specific configs
- **Monitoring**: Set up audit logging and alerts
- **Scheduling**: Integrate with cron or workflow systems

## 📚 Additional Resources

- **[User Guide](user-guide.md)** - Comprehensive usage instructions
- **[Configuration Reference](configuration.md)** - All configuration options
- **[CLI Reference](cli-reference.md)** - Complete command reference
- **[Plugin Development](plugin-development.md)** - Create custom plugins
- **[Examples](../examples/)** - Sample pipelines and configurations

---

**Ready to build your next pipeline?** Check out the [User Guide](user-guide.md) for advanced features and techniques!
