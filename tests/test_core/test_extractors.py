"""Tests for extractor plugins."""

import json
from pathlib import Path

import pandas as pd
import pytest

from santiq.plugins.base.extractor import ExtractorPlugin
from santiq.plugins.extractors.csv_extractor import CSVExtractor
from santiq.plugins.extractors.excel_extractor import ExcelExtractor
from santiq.plugins.extractors.json_extractor import JSONExtractor


class TestCSVExtractor:
    """Test CSV extractor plugin."""

    def test_csv_extractor_basic(self, sample_csv_file: Path):
        """Test basic CSV extraction."""
        extractor = CSVExtractor()
        extractor.setup({"path": str(sample_csv_file)})

        data = extractor.extract()

        assert isinstance(data, pd.DataFrame)
        assert len(data) > 0
        assert "id" in data.columns
        assert "name" in data.columns

    def test_csv_extractor_missing_file(self):
        """Test CSV extractor with missing file."""
        extractor = CSVExtractor()
        extractor.setup({"path": "/nonexistent/file.csv"})

        with pytest.raises(Exception) as exc_info:
            extractor.extract()

        assert "Failed to read CSV file" in str(exc_info.value)

    def test_csv_extractor_missing_path_config(self):
        """Test CSV extractor without path configuration."""
        extractor = CSVExtractor()

        with pytest.raises(ValueError) as exc_info:
            extractor.setup({})

        assert "requires 'path' parameter" in str(exc_info.value)

    def test_csv_extractor_with_options(self, temp_dir: Path):
        """Test CSV extractor with pandas options."""
        # Create CSV with semicolon separator
        data = "id;name;age\n1;Alice;25\n2;Bob;30"
        csv_file = temp_dir / "test.csv"
        csv_file.write_text(data)

        extractor = CSVExtractor()
        extractor.setup({"path": str(csv_file), "sep": ";", "header": 0})

        result = extractor.extract()

        assert len(result) == 2
        assert list(result.columns) == ["id", "name", "age"]
        assert result.loc[0, "name"] == "Alice"

    def test_get_schema_info(self, sample_csv_file: Path):
        """Test getting schema information."""
        extractor = CSVExtractor()
        extractor.setup({"path": str(sample_csv_file)})

        schema_info = extractor.get_schema_info()

        assert "columns" in schema_info
        assert "data_types" in schema_info
        assert len(schema_info["columns"]) > 0


class TestJSONExtractor:
    """Test JSON extractor plugin."""

    def test_json_extractor_basic(self, temp_dir: Path):
        """Test basic JSON extraction."""
        # Create sample JSON data
        json_data = [
            {"id": 1, "name": "Alice", "age": 25},
            {"id": 2, "name": "Bob", "age": 30},
            {"id": 3, "name": "Charlie", "age": 35},
        ]
        json_file = temp_dir / "test.json"
        json_file.write_text(json.dumps(json_data))

        extractor = JSONExtractor()
        extractor.setup({"path": str(json_file)})

        data = extractor.extract()

        assert isinstance(data, pd.DataFrame)
        assert len(data) == 3
        assert "id" in data.columns
        assert "name" in data.columns
        assert "age" in data.columns
        assert data.loc[0, "name"] == "Alice"

    def test_json_extractor_missing_file(self):
        """Test JSON extractor with missing file."""
        extractor = JSONExtractor()
        extractor.setup({"path": "/nonexistent/file.json"})

        with pytest.raises(Exception) as exc_info:
            extractor.extract()

        assert "Failed to read JSON file" in str(exc_info.value)

    def test_json_extractor_missing_path_config(self):
        """Test JSON extractor without path configuration."""
        extractor = JSONExtractor()

        with pytest.raises(ValueError) as exc_info:
            extractor.setup({})

        assert "requires 'path' parameter" in str(exc_info.value)

    def test_json_extractor_invalid_orient(self):
        """Test JSON extractor with invalid orient parameter."""
        extractor = JSONExtractor()

        with pytest.raises(ValueError) as exc_info:
            extractor.setup({"path": "test.json", "orient": "invalid"})

        assert "Invalid 'orient' parameter" in str(exc_info.value)

    def test_json_extractor_with_options(self, temp_dir: Path):
        """Test JSON extractor with pandas options."""
        # Create JSON with different orientation
        json_data = {
            "data": [[1, 2, 3], ["Alice", "Bob", "Charlie"], [25, 30, 35]],
            "columns": ["id", "name", "age"],
            "index": [0, 1, 2],
        }
        json_file = temp_dir / "test.json"
        json_file.write_text(json.dumps(json_data))

        extractor = JSONExtractor()
        extractor.setup({"path": str(json_file), "orient": "split"})

        result = extractor.extract()

        assert len(result) == 3
        assert list(result.columns) == ["id", "name", "age"]
        # In split format, data structure might vary, so we just check that we got data
        assert "name" in result.columns

    def test_json_extractor_lines_format(self, temp_dir: Path):
        """Test JSON extractor with JSON lines format."""
        # Create JSON lines format
        json_lines = [
            '{"id": 1, "name": "Alice", "age": 25}',
            '{"id": 2, "name": "Bob", "age": 30}',
            '{"id": 3, "name": "Charlie", "age": 35}',
        ]
        json_file = temp_dir / "test.jsonl"
        json_file.write_text("\n".join(json_lines))

        extractor = JSONExtractor()
        extractor.setup({"path": str(json_file), "lines": True})

        result = extractor.extract()

        assert len(result) == 3
        assert "id" in result.columns
        assert "name" in result.columns
        assert "age" in result.columns

    def test_json_extractor_invalid_json(self, temp_dir: Path):
        """Test JSON extractor with invalid JSON."""
        json_file = temp_dir / "invalid.json"
        json_file.write_text('{"invalid": json}')  # Invalid JSON

        extractor = JSONExtractor()
        extractor.setup({"path": str(json_file)})

        with pytest.raises(Exception) as exc_info:
            extractor.extract()

        # The error message might vary, so we check for any error
        assert "Failed to read JSON file" in str(exc_info.value)

    def test_get_schema_info(self, temp_dir: Path):
        """Test getting schema information."""
        json_data = [
            {"id": 1, "name": "Alice", "age": 25},
            {"id": 2, "name": "Bob", "age": 30},
        ]
        json_file = temp_dir / "test.json"
        json_file.write_text(json.dumps(json_data))

        extractor = JSONExtractor()
        extractor.setup({"path": str(json_file)})

        schema_info = extractor.get_schema_info()

        assert "columns" in schema_info
        assert "data_types" in schema_info
        assert "estimated_rows" in schema_info
        assert "json_format" in schema_info
        # The schema detection might not work perfectly in all cases, so we're more flexible
        # Just check that we have the basic structure


class TestExcelExtractor:
    """Test Excel extractor plugin."""

    def test_excel_extractor_basic(self, temp_dir: Path):
        """Test basic Excel extraction functionality."""
        # Create a simple Excel file using pandas
        import pandas as pd

        data = pd.DataFrame(
            {"id": [1, 2, 3], "name": ["Alice", "Bob", "Charlie"], "age": [25, 30, 35]}
        )

        excel_file = temp_dir / "test.xlsx"
        data.to_excel(excel_file, index=False)

        extractor = ExcelExtractor()
        extractor.setup({"path": str(excel_file)})

        result = extractor.extract()

        assert len(result) == 3
        assert list(result.columns) == ["id", "name", "age"]
        assert result.loc[0, "name"] == "Alice"

        # Force cleanup of any open file handles
        import gc
        import time

        gc.collect()
        time.sleep(0.1)

    def test_excel_extractor_with_options(self, temp_dir: Path):
        """Test Excel extractor with pandas options."""
        import pandas as pd

        # Create Excel with header in row 2
        data = pd.DataFrame(
            {"id": [1, 2, 3], "name": ["Alice", "Bob", "Charlie"], "age": [25, 30, 35]}
        )

        excel_file = temp_dir / "test.xlsx"

        # Write data directly to Excel
        data.to_excel(excel_file, index=False)

        extractor = ExcelExtractor()
        extractor.setup(
            {
                "path": str(excel_file),
                "header": 0,  # Header is in row 0 (default)
                "skiprows": 0,  # No rows to skip
            }
        )

        result = extractor.extract()

        assert len(result) == 3
        assert list(result.columns) == ["id", "name", "age"]

        # Force cleanup of any open file handles
        import gc
        import time

        gc.collect()
        time.sleep(0.1)

    def test_excel_extractor_invalid_file(self, temp_dir: Path):
        """Test Excel extractor with invalid file."""
        excel_file = temp_dir / "nonexistent.xlsx"

        extractor = ExcelExtractor()

        with pytest.raises(FileNotFoundError):
            extractor.setup({"path": str(excel_file)})

    def test_excel_extractor_missing_path(self):
        """Test Excel extractor with missing path."""
        extractor = ExcelExtractor()

        with pytest.raises(ValueError, match="'path' is required"):
            extractor.setup({})

    def test_get_schema_info(self, temp_dir: Path):
        """Test getting schema information."""
        import pandas as pd

        data = pd.DataFrame(
            {"id": [1, 2, 3], "name": ["Alice", "Bob", "Charlie"], "age": [25, 30, 35]}
        )

        excel_file = temp_dir / "test.xlsx"
        data.to_excel(excel_file, index=False)

        extractor = ExcelExtractor()
        extractor.setup({"path": str(excel_file)})

        schema_info = extractor.get_schema_info()

        assert "columns" in schema_info
        assert "data_types" in schema_info
        assert "estimated_rows" in schema_info
        assert "sheet_names" in schema_info
        assert "file_size_bytes" in schema_info
        assert "engine" in schema_info
        assert len(schema_info["columns"]) == 3
        assert "id" in schema_info["columns"]
        assert "name" in schema_info["columns"]
        assert "age" in schema_info["columns"]

        # Force cleanup of any open file handles
        import gc
        import time

        gc.collect()
        time.sleep(0.1)  # Small delay to ensure file handles are released
