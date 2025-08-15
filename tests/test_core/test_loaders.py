"""Tests for loader plugins."""

import pytest
import pandas as pd
from pathlib import Path

from santiq.plugins.loaders.csv_loader import CSVLoader
from santiq.plugins.base.loader import LoadResult


class TestCSVLoader:
    """Test CSV loader plugin."""
    
    def test_basic_loading(self, temp_dir: Path, sample_data: pd.DataFrame):
        """Test basic CSV loading functionality."""
        output_path = temp_dir / "output.csv"
        
        loader = CSVLoader()
        loader.setup({"path": str(output_path)})
        
        result = loader.load(sample_data)
        
        assert isinstance(result, LoadResult)
        assert result.success is True
        assert result.rows_loaded == len(sample_data)
        assert output_path.exists()
        
        # Verify the saved data
        loaded_data = pd.read_csv(output_path)
        assert len(loaded_data) == len(sample_data)
        assert list(loaded_data.columns) == list(sample_data.columns)
    
    def test_loading_with_options(self, temp_dir: Path, sample_data: pd.DataFrame):
        """Test CSV loading with pandas options."""
        output_path = temp_dir / "output.csv"
        
        loader = CSVLoader()
        loader.setup({
            "path": str(output_path),
            "sep": ";",
            "index": True  # Include index
        })
        
        result = loader.load(sample_data)
        
        assert result.success is True
        assert output_path.exists()
        
        # Check that separator was used
        content = output_path.read_text()
        assert ";" in content
    
    def test_loading_missing_directory(self, temp_dir: Path, sample_data: pd.DataFrame):
        """Test loading to a path where parent directory doesn't exist."""
        output_path = temp_dir / "nested" / "subdir" / "output.csv"
        
        loader = CSVLoader()
        loader.setup({"path": str(output_path)})
        
        result = loader.load(sample_data)
        
        assert result.success is True
        assert output_path.exists()  # Directory should be created
        assert output_path.parent.exists()
    
    def test_loading_failure(self, sample_data: pd.DataFrame):
        """Test handling of loading failures."""
        # Try to write to an invalid path
        loader = CSVLoader()
        loader.setup({"path": "/invalid/path/that/cannot/be/created.csv"})
        
        result = loader.load(sample_data)
        
        assert result.success is False
        assert result.rows_loaded == 0
        assert "error" in result.metadata
    
    def test_incremental_support(self):
        """Test incremental loading support check."""
        loader = CSVLoader()
        
        # Default mode doesn't support incremental
        loader.setup({"path": "/test.csv"})
        assert not loader.supports_incremental()
        
        # Append mode supports incremental
        loader.setup({"path": "/test.csv", "mode": "a"})
        assert loader.supports_incremental()
    
    def test_metadata_information(self, temp_dir: Path, sample_data: pd.DataFrame):
        """Test that loader provides useful metadata."""
        output_path = temp_dir / "output.csv"
        
        loader = CSVLoader()
        loader.setup({"path": str(output_path)})
        
        result = loader.load(sample_data)
        
        assert "output_path" in result.metadata
        assert "columns" in result.metadata
        assert "file_size_bytes" in result.metadata
        
        assert result.metadata["output_path"] == str(output_path)
        assert result.metadata["columns"] == list(sample_data.columns)
        assert result.metadata["file_size_bytes"] > 0