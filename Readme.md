
# Santiq

A lightweight, modular, plugin-first ETL platform designed for individuals, small businesses, and scalable up to enterprise workloads.

## Features

- 🔌 **Plugin-First Architecture**: Everything is a plugin, even core functionality
- 🧠 **Smart Data Profiling**: Automatic issue detection with context-aware fix suggestions
- ⚡ **Multiple Execution Modes**: Manual, half-automatic, and controlled-automatic
- 📊 **Learning System**: Remembers your preferences for future pipeline runs
- 🛡️ **Enterprise Ready**: Comprehensive audit logging and error handling
- 🚀 **Performance Optimized**: Hybrid memory/disk usage based on data size

## Quick Start

### Installation

```bash
pip install santiq
```

### Create Your First Pipeline

```bash
# Initialize a new pipeline
santiq init my-pipeline

# Edit my-pipeline.yml to configure your data sources
# Set environment variables
export INPUT_PATH=/path/to/your/data
export OUTPUT_PATH=/path/to/output

# Run the pipeline
santiq run pipeline my-pipeline.yml --mode half-auto
```

### Example Pipeline Configuration

```yaml
name: "Data Cleaning Pipeline"
description: "Clean customer data and export to CSV"

extractor:
  plugin: csv_extractor
  params:
    path: "${INPUT_PATH}/customers.csv"
    header: 0

profilers:
  - plugin: basic_profiler

transformers:
  - plugin: basic_cleaner
    params:
      drop_nulls: true
      drop_duplicates: true
      convert_types:
        age: numeric
        signup_date: datetime

loaders:
  - plugin: csv_loader
    params:
      path: "${OUTPUT_PATH}/cleaned_customers.csv"
```

## Execution Modes

- **Manual**: Review and manually apply each suggested fix
- **Half-Auto**: Bulk approve/reject suggestions, preferences saved for future runs
- **Controlled-Auto**: Automatically apply previously approved fix types

## Plugin Management

```bash
# List available plugins
santiq plugin list

# Install additional plugins
santiq plugin install santiq-plugin-postgres
santiq plugin install santiq-plugin-advanced-cleaner

# Remove plugins
santiq plugin remove santiq-plugin-csv
```

## Development

### Setting Up Development Environment

```bash
git clone https://github.com/yourusername/santiq.git
cd santiq
pip install -e ".[dev]"
pre-commit install
```

### Running Tests

```bash
pytest
pytest --cov=santiq tests/  # With coverage
```

### Creating a Plugin

See [Plugin Development Guide](docs/plugin_development.md) for detailed instructions.

## Architecture

```bash
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Extractors    │    │    Profilers     │    │  Transformers   │
│  ┌───────────┐  │    │  ┌────────────┐  │    │  ┌───────────┐  │
│  │    CSV    │  │    │  │   Basic    │  │    │  │  Cleaner  │  │
│  │  Database │  │────┤  │  Advanced  │  ├────┤  │   AI Fix  │  │
│  │    API    │  │    │  │   Schema   │  │    │  │  Custom   │  │
│  └───────────┘  │    │  └────────────┘  │    │  └───────────┘  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                        │                        │
         └────────────────────────┼────────────────────────┘
                                  │
                    ┌─────────────────────────┐
                    │     Santiq Engine       │
                    │  ┌─────────────────┐    │
                    │  │ Plugin Manager  │    │
                    │  │ Audit Logger    │    │
                    │  │ Config Manager  │    │
                    │  └─────────────────┘    │
                    └─────────────────────────┘
                                  │
                    ┌─────────────────────────┐
                    │       Loaders           │
                    │  ┌─────────────────┐    │
                    │  │      CSV        │    │
                    │  │    Database     │    │
                    │  │   Cloud Storage │    │
                    │  └─────────────────┘    │
                    └─────────────────────────┘
```

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT License - see [LICENSE](LICENSE) file for details.
