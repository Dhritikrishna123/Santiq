"""Tests for extractor plugins."""

import pytest
import pandas as pd
from pathlib import Path

from santiq.plugins.extractors.csv_extractor import CSVExtractor
from santiq.plugins.base.extractor import ExtractorPlugin


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
        extractor.setup({
            "path": str(csv_file),
            "sep": ";",
            "header": 0
        })
        
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