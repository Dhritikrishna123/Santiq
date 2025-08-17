
# Santiq

<div align="center">

![Santiq Logo](https://img.shields.io/badge/Santiq-ETL%20Platform-blue?style=for-the-badge&logo=python)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PyPI version](https://badge.fury.io/py/santiq.svg)](https://badge.fury.io/py/santiq)

**A lightweight, modular, plugin-first ETL platform designed for individuals, small businesses, and scalable up to enterprise workloads.**

[Quick Start](#quick-start) • [Documentation](https://santiq.readthedocs.io/) • [Examples](examples/) • [Contributing](CONTRIBUTING.md)

</div>

---

## 🚀 What is Santiq?

Santiq is a modern ETL (Extract, Transform, Load) platform that makes data processing simple, reliable, and extensible. Built with a plugin-first architecture, Santiq allows you to:

- **Extract** data from any source (files, databases, APIs, cloud services)
- **Profile** data to automatically detect quality issues
- **Transform** data with intelligent cleaning and validation
- **Load** data to any destination with full audit trails

### ✨ Key Features

- 🔌 **Plugin-First Architecture**: Everything is a plugin, even core functionality
- 🧠 **Smart Data Profiling**: Automatic issue detection with context-aware fix suggestions
- ⚡ **Multiple Execution Modes**: Manual, half-automatic, and controlled-automatic
- 📊 **Learning System**: Remembers your preferences for future pipeline runs
- 🛡️ **Enterprise Ready**: Comprehensive audit logging and error handling
- 🚀 **Performance Optimized**: Hybrid memory/disk usage based on data size
- 🔧 **Extensible**: Easy to create custom plugins for any data source or transformation

## 🏃‍♂️ Quick Start

### Installation

```bash
pip install santiq
```

### Your First Pipeline

```bash
# Initialize a new pipeline
santiq init my-first-pipeline

# Edit the generated configuration file
# my-first-pipeline.yml

# Run the pipeline
santiq run pipeline my-first-pipeline.yml
```

### Example Pipeline Configuration

```yaml
name: "Customer Data Cleaning"
description: "Clean and validate customer data from CSV"

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
      convert_types:
        age: numeric
        signup_date: datetime

loaders:
  - plugin: csv_loader
    params:
      path: "${OUTPUT_PATH}/cleaned_customers.csv"
```

## 📚 Documentation

### For Users
- **[Getting Started Guide](docs/getting-started.md)** - Complete beginner's guide
- **[User Guide](docs/user-guide.md)** - Comprehensive usage instructions
- **[Configuration Reference](docs/configuration.md)** - Pipeline configuration options
- **[CLI Reference](docs/cli-reference.md)** - Command-line interface documentation

### For Developers
- **[Plugin Development Guide](docs/plugin-development.md)** - Create custom plugins
- **[API Reference](docs/api-reference.md)** - Core API documentation
- **[Plugin Examples](docs/plugin-examples.md)** - Sample plugin implementations

### For Administrators
- **[Installation Guide](docs/installation.md)** - Production deployment
- **[Configuration Management](docs/configuration-management.md)** - Environment setup
- **[Monitoring & Logging](docs/monitoring.md)** - Audit trails and observability

## 🔌 Plugin Ecosystem

Santiq comes with built-in plugins and supports a growing ecosystem:

### Built-in Plugins
- **Extractors**: CSV, JSON, Excel files
- **Profilers**: Basic data quality analysis
- **Transformers**: Data cleaning, validation, type conversion
- **Loaders**: CSV, JSON, database outputs

### Community Plugins
```bash
# Install community plugins
santiq plugin install santiq-plugin-postgres
santiq plugin install santiq-plugin-elasticsearch

# List available plugins
santiq plugin list --available
```

## 🎯 Use Cases

### Data Quality Assurance
```bash
# Profile data and get quality report
santiq run pipeline data-quality.yml --mode manual
```

### Automated Data Processing
```bash
# Run with automatic fix application
santiq run pipeline production.yml --mode controlled-auto
```

### Data Migration
```bash
# Migrate data between systems
santiq run pipeline migration.yml --mode half-auto
```

## 🏗️ Architecture

```
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

## 🛠️ Development

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

See [Plugin Development Guide](docs/plugin-development.md) for detailed instructions.

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Ways to Contribute
- 🐛 **Report Bugs**: Create detailed issue reports
- 💡 **Suggest Features**: Propose new functionality
- 🔧 **Submit Code**: Fix bugs or add features
- 📚 **Improve Docs**: Help make documentation better
- 🔌 **Create Plugins**: Build plugins for new data sources

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [Pandas](https://pandas.pydata.org/) for data manipulation
- Powered by [Typer](https://typer.tiangolo.com/) for CLI
- Styled with [Rich](https://rich.readthedocs.io/) for beautiful output
- Validated with [Pydantic](https://pydantic-docs.helpmanual.io/) for data validation

---

<div align="center">

**Made with ❤️ by the Santiq Community**

[GitHub](https://github.com/yourusername/santiq) • [Issues](https://github.com/yourusername/santiq/issues) • [Discussions](https://github.com/yourusername/santiq/discussions)

</div>
