"""Shared test fixtures and configuration."""

import tempfile
from pathlib import Path
from typing import Any, Dict, Generator

import pandas as pd
import pytest

from santiq.core.audit import AuditLogger
from santiq.core.config import ConfigManager
from santiq.core.engine import ETLEngine
from santiq.core.plugin_manager import PluginManager


@pytest.fixture
def sample_data() -> pd.DataFrame:
    """Create sample data for testing."""
    return pd.DataFrame({
        "id": [1, 2, 3, 4, 5, 2],  # Duplicate ID
        "name": ["Alice", "Bob", None, "Diana", "Eve", "Bob"],  # Null value
        "age": ["25", "30", "35", "invalid", "28", "30"],  # Type issues
        "salary": [50000, 60000, 70000, 80000, 55000, 60000]
    })


@pytest.fixture
def clean_sample_data() -> pd.DataFrame:
    """Create clean sample data for testing."""
    return pd.DataFrame({
        "id": [1, 2, 3, 4, 5],
        "name": ["Alice", "Bob", "Charlie", "Diana", "Eve"],
        "age": [25, 30, 35, 40, 28],
        "salary": [50000, 60000, 70000, 80000, 55000]
    })


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def sample_csv_file(temp_dir: Path, sample_data: pd.DataFrame) -> Path:
    """Create a sample CSV file for testing."""
    csv_file = temp_dir / "sample.csv"
    sample_data.to_csv(csv_file, index=False)
    return csv_file


@pytest.fixture
def config_manager() -> ConfigManager:
    """Create a config manager for testing."""
    return ConfigManager()


@pytest.fixture
def plugin_manager() -> PluginManager:
    """Create a plugin manager for testing."""
    return PluginManager()


@pytest.fixture
def audit_logger(temp_dir: Path) -> AuditLogger:
    """Create an audit logger for testing."""
    return AuditLogger(str(temp_dir / "test_audit.jsonl"))


@pytest.fixture
def etl_engine(temp_dir: Path) -> ETLEngine:
    """Create an ETL engine for testing."""
    return ETLEngine(audit_log_file=str(temp_dir / "test_audit.jsonl"))


@pytest.fixture
def sample_pipeline_config(temp_dir: Path) -> Dict[str, Any]:
    """Create a sample pipeline configuration."""
    input_file = temp_dir / "input.csv"
    output_file = temp_dir / "output.csv"
    
    return {
        "name": "test_pipeline",
        "description": "Test pipeline for unit tests",
        "extractor": {
            "plugin": "csv_extractor",
            "params": {"path": str(input_file)}
        },
        "profilers": [
            {
                "plugin": "basic_profiler",
                "params": {}
            }
        ],
        "transformers": [
            {
                "plugin": "basic_cleaner",
                "params": {
                    "drop_nulls": True,
                    "drop_duplicates": True
                }
            }
        ],
        "loaders": [
            {
                "plugin": "csv_loader",
                "params": {"path": str(output_file)}
            }
        ]
    }


@pytest.fixture
def sample_pipeline_yaml(temp_dir: Path, sample_csv_file: Path) -> Path:
    """Create a sample pipeline YAML file."""
    config_content = f"""name: "test_pipeline"
description: "Test pipeline for integration tests"

extractor:
  plugin: csv_extractor
  params:
    path: "{sample_csv_file}"

profilers:
  - plugin: basic_profiler
    params: {{}}

transformers:
  - plugin: basic_cleaner
    params:
      drop_nulls: true
      drop_duplicates: true

loaders:
  - plugin: csv_loader
    params:
      path: "{temp_dir}/output.csv"
"""
    
    config_file = temp_dir / "test_pipeline.yml"
    config_file.write_text(config_content)
    return config_file
