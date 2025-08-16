"""Tests for profiler plugins."""

import pandas as pd
import pytest

from santiq.plugins.base.profiler import ProfileResult
from santiq.plugins.profilers.basic_profiler import BasicProfiler


class TestBasicProfiler:
    """Test basic profiler plugin."""
    
    def test_basic_profiling(self, problematic_data: pd.DataFrame):
        """Test basic data profiling functionality."""
        profiler = BasicProfiler()
        profiler.setup({})
        
        result = profiler.profile(problematic_data)
        
        assert isinstance(result, ProfileResult)
        assert len(result.issues) > 0
        assert len(result.suggestions) > 0
        assert "total_rows" in result.summary
    
    def test_null_detection(self):
        """Test null value detection."""
        data = pd.DataFrame({
            "col1": [1, 2, None, 4],
            "col2": [None, "b", "c", "d"]
        })
        
        profiler = BasicProfiler()
        profiler.setup({})
        result = profiler.profile(data)
        
        null_issues = [issue for issue in result.issues if issue["type"] == "null_values"]
        assert len(null_issues) == 2  # Both columns have nulls
        
        # Check specific null counts
        col1_issue = next(issue for issue in null_issues if issue["column"] == "col1")
        assert col1_issue["count"] == 1
        assert col1_issue["percentage"] == 25.0
    
    def test_duplicate_detection(self):
        """Test duplicate row detection."""
        data = pd.DataFrame({
            "id": [1, 2, 3, 2, 4],  # Row with id=2 is duplicated
            "name": ["A", "B", "C", "B", "D"]
        })
        
        profiler = BasicProfiler()
        profiler.setup({})
        result = profiler.profile(data)
        
        dup_issues = [issue for issue in result.issues if issue["type"] == "duplicate_rows"]
        assert len(dup_issues) == 1
        assert dup_issues[0]["count"] == 1  # One duplicate row
    
    def test_type_mismatch_detection(self):
        """Test data type mismatch detection."""
        data = pd.DataFrame({
            "numeric_as_string": ["1", "2", "3", "4"],  # Should be numeric
            "actual_string": ["a", "b", "c", "d"]  # Should stay string
        })
        
        profiler = BasicProfiler()
        profiler.setup({})
        result = profiler.profile(data)
        
        type_issues = [issue for issue in result.issues if issue["type"] == "type_mismatch"]
        assert len(type_issues) == 1
        assert type_issues[0]["column"] == "numeric_as_string"
        assert type_issues[0]["suggested_type"] == "numeric"
    
    def test_clean_data_profiling(self):
        """Test profiling clean data (no issues)."""
        data = pd.DataFrame({
            "id": [1, 2, 3, 4],
            "name": ["Alice", "Bob", "Charlie", "Diana"],
            "score": [85.5, 92.0, 78.5, 88.0]
        })
        
        profiler = BasicProfiler()
        profiler.setup({})
        result = profiler.profile(data)
        
        # Should have no critical issues
        critical_issues = [issue for issue in result.issues 
                          if issue.get("severity") in ["high", "medium"]]
        assert len(critical_issues) == 0
    
    def test_profiling_suggestions(self, problematic_data: pd.DataFrame):
        """Test that profiler generates appropriate suggestions."""
        profiler = BasicProfiler()
        profiler.setup({})
        result = profiler.profile(problematic_data)
        
        suggestion_types = {suggestion["fix_type"] for suggestion in result.suggestions}
        
        # Should suggest fixes for detected issues
        assert "drop_nulls" in suggestion_types
        assert len([s for s in result.suggestions if s["fix_type"] == "drop_nulls"]) > 0
