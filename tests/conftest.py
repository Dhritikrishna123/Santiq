"""Shared test fixtures and configuration."""

import tempfile
import json
import sys
from pathlib import Path
from typing import Any, Dict, Generator, List
import pytest
import pandas as pd
from unittest.mock import Mock, patch

from santiq.core.audit import AuditLogger
from santiq.core.config import ConfigManager, PipelineConfig
from santiq.core.engine import ETLEngine
from santiq.core.plugin_manager import PluginManager
from santiq.plugins.base.extractor import ExtractorPlugin
from santiq.plugins.base.transformer import TransformerPlugin, TransformResult


@pytest.fixture
def sample_data() -> pd.DataFrame:
    """Create sample data for testing."""
    return pd.DataFrame({
        "id": [1, 2, 3, 4, 5, 2],  # Duplicate ID
        "name": ["Alice", "Bob", None, "Diana", "Eve", "Bob"],  # Null value
        "age": ["25", "30", "35", "invalid", "28", "30"],  # Type issues
        "salary": [50000, 60000, 70000, 80000, 55000, 60000],
        "email": ["alice@test.com", "bob@test.com", "charlie@test.com", 
                 "diana@test.com", "eve@test.com", "bob@test.com"]
    })


@pytest.fixture
def problematic_data() -> pd.DataFrame:
    """Data with various quality issues."""
    return pd.DataFrame({
        "id": [1, 2, None, 4, 5, 2, 7],  # Null and duplicate
        "name": ["Alice", "", None, "Diana", "Eve", "Bob", "Frank"],
        "age": [-5, 30, 150, "invalid", 28, 30, None],  # Invalid ages
        "score": [85.5, 92.0, 78.5, None, 88.0, 92.0, "N/A"]  # Mixed types
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


# Test plugin classes for compatibility testing
class TestExtractor(ExtractorPlugin):
    """Test extractor for plugin compatibility testing."""
    __plugin_name__ = "Test Extractor"
    __api_version__ = "1.0"
    __description__ = "Test extractor for compatibility testing"
    
    def extract(self) -> pd.DataFrame:
        return pd.DataFrame({"test_col": [1, 2, 3]})


class TestTransformer(TransformerPlugin):
    """Test transformer for plugin compatibility testing."""
    __plugin_name__ = "Test Transformer"
    __api_version__ = "1.0" 
    __description__ = "Test transformer for compatibility testing"
    
    def transform(self, data: pd.DataFrame) -> TransformResult:
        # Simple transformation - add a new column
        result_data = data.copy()
        result_data["transformed"] = True
        return TransformResult(result_data, [{"fix_type": "test_transform", "description": "Added transformed column"}])


class IncompatiblePlugin(ExtractorPlugin):
    """Plugin with incompatible API version."""
    __plugin_name__ = "Incompatible Plugin"
    __api_version__ = "999.0"  # Incompatible version
    __description__ = "Plugin with incompatible API version"
    
    def extract(self) -> pd.DataFrame:
        return pd.DataFrame({"col": [1]})


@pytest.fixture
def test_plugin_classes():
    """Provide test plugin classes."""
    return {
        "compatible_extractor": TestExtractor,
        "compatible_transformer": TestTransformer,
        "incompatible_extractor": IncompatiblePlugin
    }
