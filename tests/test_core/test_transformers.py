"""Tests for transformer plugins."""

import pytest
import pandas as pd

from santiq.plugins.transformers.basic_cleaner import BasicCleaner
from santiq.plugins.base.transformer import TransformResult


class TestBasicCleaner:
    """Test basic cleaner transformer plugin."""
    
    def test_drop_nulls(self):
        """Test dropping null values."""
        data = pd.DataFrame({
            "id": [1, 2, None, 4],
            "name": ["Alice", "Bob", None, "Diana"]
        })
        
        cleaner = BasicCleaner()
        cleaner.setup({"drop_nulls": True})
        
        result = cleaner.transform(data)
        
        assert isinstance(result, TransformResult)
        assert len(result.data) == 2  # Only rows without any nulls
        assert result.data.isnull().sum().sum() == 0
        assert len(result.applied_fixes) > 0
        assert result.applied_fixes[0]["fix_type"] == "drop_nulls"
    
    def test_drop_nulls_specific_columns(self):
        """Test dropping nulls from specific columns only."""
        data = pd.DataFrame({
            "id": [1, 2, None, 4],
            "name": ["Alice", "Bob", "Charlie", None],
            "optional": [None, "X", None, "Y"]
        })
        
        cleaner = BasicCleaner()
        cleaner.setup({"drop_nulls": ["id"]})  # Only drop nulls from id column
        
        result = cleaner.transform(data)
        
        # Should only drop the row where id is null
        assert len(result.data) == 3
        assert result.data["id"].isnull().sum() == 0
        assert result.data["name"].isnull().sum() == 1  # Diana row still has null name
        assert result.data["optional"].isnull().sum() == 2  # Optional nulls preserved
    
    def test_drop_duplicates(self):
        """Test removing duplicate rows."""
        data = pd.DataFrame({
            "id": [1, 2, 3, 2, 4],  # Duplicate row with id=2
            "name": ["Alice", "Bob", "Charlie", "Bob", "Diana"]
        })
        
        cleaner = BasicCleaner()
        cleaner.setup({"drop_duplicates": True})
        
        result = cleaner.transform(data)
        
        assert len(result.data) == 4  # One duplicate removed
        assert len(result.applied_fixes) > 0
        assert result.applied_fixes[0]["fix_type"] == "drop_duplicates"
    
    def test_type_conversion(self):
        """Test data type conversions."""
        data = pd.DataFrame({
            "numeric_string": ["1", "2", "3"],
            "date_string": ["2023-01-01", "2023-01-02", "2023-01-03"],
            "category_string": ["A", "B", "A"]
        })
        
        cleaner = BasicCleaner()
        cleaner.setup({
            "convert_types": {
                "numeric_string": "numeric",
                "date_string": "datetime",
                "category_string": "category"
            }
        })
        
        result = cleaner.transform(data)
        
        assert pd.api.types.is_numeric_dtype(result.data["numeric_string"])
        assert pd.api.types.is_datetime64_any_dtype(result.data["date_string"])
        assert pd.api.types.is_categorical_dtype(result.data["category_string"])
        
        # Should have applied fixes for each conversion
        type_fixes = [fix for fix in result.applied_fixes if fix["fix_type"] == "convert_type"]
        assert len(type_fixes) == 3
    
    def test_combined_cleaning(self, problematic_data: pd.DataFrame):
        """Test combined cleaning operations."""
        cleaner = BasicCleaner()
        cleaner.setup({
            "drop_nulls": True,
            "drop_duplicates": True,
            "convert_types": {
                "score": "numeric"  # Convert score column to numeric
            }
        })
        
        result = cleaner.transform(problematic_data)
        
        # Should apply multiple fixes
        fix_types = {fix["fix_type"] for fix in result.applied_fixes}
        assert len(fix_types) >= 2  # At least drop_nulls and drop_duplicates
        
        # Data should be cleaner
        assert result.data.isnull().sum().sum() == 0  # No nulls
        assert len(result.data) < len(problematic_data)  # Some rows removed
    
    def test_can_handle_issue(self):
        """Test issue handling capability check."""
        cleaner = BasicCleaner()
        cleaner.setup({})
        
        assert cleaner.can_handle_issue("null_values")
        assert cleaner.can_handle_issue("duplicate_rows")
        assert cleaner.can_handle_issue("type_mismatch")
        assert not cleaner.can_handle_issue("unknown_issue_type")
    
    def test_suggest_fixes(self, problematic_data: pd.DataFrame):
        """Test fix suggestions generation."""
        issues = [
            {"type": "null_values", "column": "name", "count": 2},
            {"type": "duplicate_rows", "count": 1},
            {"type": "type_mismatch", "column": "age", "suggested_type": "numeric"}
        ]
        
        cleaner = BasicCleaner()
        cleaner.setup({})
        
        suggestions = cleaner.suggest_fixes(problematic_data, issues)
        
        assert len(suggestions) == 3
        
        suggestion_types = {s["fix_type"] for s in suggestions}
        assert "drop_nulls" in suggestion_types
        assert "drop_duplicates" in suggestion_types
        assert "convert_type" in suggestion_types
