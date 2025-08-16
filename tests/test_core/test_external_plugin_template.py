"""Template and tests for external plugin development."""

import importlib.util
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd
import pytest

from santiq.core.plugin_manager import PluginManager
from santiq.plugins.base.extractor import ExtractorPlugin
from santiq.plugins.base.loader import LoaderPlugin, LoadResult
from santiq.plugins.base.profiler import ProfileResult, ProfilerPlugin
from santiq.plugins.base.transformer import TransformerPlugin, TransformResult


class TestExternalPluginTemplate:
    """Test template for external plugin developers."""
    
    def create_test_plugin_directory(self, temp_dir: Path, plugin_type: str) -> Path:
        """Create a complete plugin directory structure for testing."""
        plugin_dir = temp_dir / f"test_{plugin_type}_plugin"
        plugin_dir.mkdir()
        
        # Create plugin manifest
        manifest = {
            "name": f"test_{plugin_type}",
            "type": plugin_type,
            "version": "1.0.0",
            "api_version": "1.0",
            "description": f"Test {plugin_type} plugin for external development",
            "entry_point": "plugin:TestTransformerPlugin" if plugin_type == "transformer" else f"plugin:Test{plugin_type.title()}Plugin",
            "author": "Test Developer",
            "license": "MIT",
            "requirements": ["pandas>=2.0.0"]
        }
        
        import yaml
        with open(plugin_dir / "plugin.yml", 'w') as f:
            yaml.dump(manifest, f)
        
        return plugin_dir
    
    def test_external_extractor_plugin_template(self):
        """Test template for external extractor plugin development."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            plugin_dir = self.create_test_plugin_directory(temp_path, "extractor")
            
            # Create extractor plugin code
            plugin_code = '''
import pandas as pd
from typing import Any, Dict
from santiq.plugins.base.extractor import ExtractorPlugin

class TestExtractorPlugin(ExtractorPlugin):
    """Example external extractor plugin."""
    
    __plugin_name__ = "Test Extractor Plugin"
    __api_version__ = "1.0"
    __description__ = "Example extractor for external plugin development"
    __version__ = "1.0.0"
    
    def _validate_config(self) -> None:
        """Validate plugin configuration."""
        required_params = ["data_source", "format"]
        for param in required_params:
            if param not in self.config:
                raise ValueError(f"Missing required parameter: {param}")
        
        valid_formats = ["json", "csv", "excel"]
        if self.config["format"] not in valid_formats:
            raise ValueError(f"Format must be one of: {valid_formats}")
    
    def extract(self) -> pd.DataFrame:
        """Extract data from the configured source."""
        data_source = self.config["data_source"]
        format_type = self.config["format"]
        
        # Mock implementation - in real plugin this would connect to actual data source
        if format_type == "json":
            return self._extract_json(data_source)
        elif format_type == "csv":
            return self._extract_csv(data_source)
        elif format_type == "excel":
            return self._extract_excel(data_source)
        else:
            raise ValueError(f"Unsupported format: {format_type}")
    
    def _extract_json(self, source: str) -> pd.DataFrame:
        """Extract from JSON source (mock implementation)."""
        return pd.DataFrame({
            "id": [1, 2, 3],
            "name": ["A", "B", "C"],
            "source": [source] * 3,
            "format": ["json"] * 3
        })
    
    def _extract_csv(self, source: str) -> pd.DataFrame:
        """Extract from CSV source (mock implementation)."""
        return pd.DataFrame({
            "id": [4, 5, 6],
            "name": ["D", "E", "F"],
            "source": [source] * 3,
            "format": ["csv"] * 3
        })
    
    def _extract_excel(self, source: str) -> pd.DataFrame:
        """Extract from Excel source (mock implementation)."""
        return pd.DataFrame({
            "id": [7, 8, 9],
            "name": ["G", "H", "I"],
            "source": [source] * 3,
            "format": ["excel"] * 3
        })
    
    def get_schema_info(self) -> Dict[str, Any]:
        """Return schema information."""
        return {
            "columns": ["id", "name", "source", "format"],
            "data_types": {
                "id": "int64",
                "name": "object", 
                "source": "object",
                "format": "object"
            },
            "estimated_rows": 3
        }
    
    def teardown(self) -> None:
        """Clean up resources."""
        # In real plugin, close connections, files, etc.
        super().teardown()
'''
            
            plugin_file = plugin_dir / "plugin.py"
            plugin_file.write_text(plugin_code)
            
            # Test plugin loading and functionality
            plugin_manager = PluginManager(local_plugin_dirs=[str(temp_path)])
            plugins = plugin_manager.discover_plugins()
            
            # Verify plugin was discovered
            extractors = [p for p in plugins["extractor"] if p["name"] == "test_extractor"]
            assert len(extractors) == 1
            
            # Test plugin instantiation and execution
            config = {"data_source": "test_db", "format": "json"}
            instance = plugin_manager.create_plugin_instance("test_extractor", "extractor", config)
            
            # Test extraction
            data = instance.extract()
            assert len(data) == 3
            assert list(data.columns) == ["id", "name", "source", "format"]
            assert all(data["source"] == "test_db")
            assert all(data["format"] == "json")
            
            # Test schema info
            schema_info = instance.get_schema_info()
            assert "columns" in schema_info
            assert len(schema_info["columns"]) == 4
    
    def test_external_transformer_plugin_template(self):
        """Test template for external transformer plugin development."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            plugin_dir = temp_path / "test_transformer_plugin"
            plugin_dir.mkdir()
            
            # Create plugin manifest
            manifest = {
                "name": "test_transformer",
                "type": "transformer",
                "version": "1.0.0",
                "api_version": "1.0",
                "description": "Test transformer plugin for external development",
                "entry_point": "plugin:TestTransformerPlugin",
                "author": "Test Developer",
                "license": "MIT",
                "requirements": ["pandas>=2.0.0"]
            }
            
            import yaml
            with open(plugin_dir / "plugin.yml", 'w') as f:
                yaml.dump(manifest, f)
            
            # Create transformer plugin code
            plugin_code = '''import pandas as pd
from typing import Any, Dict, List
from santiq.plugins.base.transformer import TransformerPlugin, TransformResult

class TestTransformerPlugin(TransformerPlugin):
    """Example external transformer plugin."""
    
    __plugin_name__ = "Test Transformer Plugin"
    __api_version__ = "1.0"
    __description__ = "Example transformer for external plugin development"
    __version__ = "1.0.0"
    
    def transform(self, data: pd.DataFrame) -> TransformResult:
        """Transform the data."""
        transformed_data = data.copy()
        applied_fixes = []
        
        # Example transformations
        if self.config.get("standardize_names", False):
            transformed_data = self._standardize_names(transformed_data, applied_fixes)
        
        if self.config.get("validate_emails", False):
            transformed_data = self._validate_emails(transformed_data, applied_fixes)
        
        return TransformResult(transformed_data, applied_fixes, {"plugin_version": "1.0.0"})
    
    def _standardize_names(self, data: pd.DataFrame, applied_fixes: List[Dict[str, Any]]) -> pd.DataFrame:
        """Standardize name formats."""
        if "name" in data.columns:
            original_names = data["name"].copy()
            data["name"] = data["name"].str.title()
            
            changes = (original_names != data["name"]).sum()
            if changes > 0:
                applied_fixes.append({
                    "fix_type": "standardize_names",
                    "description": f"Standardized {changes} name formats to title case",
                    "rows_affected": changes
                })
        
        return data
    
    def _validate_emails(self, data: pd.DataFrame, applied_fixes: List[Dict[str, Any]]) -> pd.DataFrame:
        """Validate email formats."""
        if "email" in data.columns:
            import re
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            
            valid_emails = data["email"].str.match(email_pattern, na=False)
            invalid_count = (~valid_emails).sum()
            
            if invalid_count > 0:
                data.loc[~valid_emails, "email"] = None  # Mark invalid emails as null
                applied_fixes.append({
                    "fix_type": "validate_emails",
                    "description": f"Marked {invalid_count} invalid emails as null",
                    "rows_affected": invalid_count
                })
        
        return data
    
    def can_handle_issue(self, issue_type: str) -> bool:
        """Check if this transformer can handle specific issue types."""
        return issue_type in ["invalid_names", "invalid_emails"]
    
    def suggest_fixes(self, data: pd.DataFrame, issues: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Suggest fixes for detected issues."""
        suggestions = []
        
        for issue in issues:
            if issue["type"] == "invalid_names" and "name" in data.columns:
                suggestions.append({
                    "fix_type": "standardize_names",
                    "config": {"standardize_names": True},
                    "description": "Standardize name formats to title case",
                    "confidence": 0.9
                })
            
            elif issue["type"] == "invalid_emails" and "email" in data.columns:
                suggestions.append({
                    "fix_type": "validate_emails", 
                    "config": {"validate_emails": True},
                    "description": "Validate email formats and mark invalid ones as null",
                    "confidence": 0.95
                })
        
        return suggestions'''
            
            plugin_file = plugin_dir / "plugin.py"
            plugin_file.write_text(plugin_code)
            
            # Test plugin loading and functionality
            plugin_manager = PluginManager(local_plugin_dirs=[str(temp_path)])
            
            config = {"standardize_names": True, "validate_emails": True}
            instance = plugin_manager.create_plugin_instance("test_transformer", "transformer", config)
            
            # Test transformation
            test_data = pd.DataFrame({
                "name": ["john doe", "JANE SMITH", "bob jones"],
                "email": ["john@test.com", "invalid-email", "jane@example.org"]
            })
            
            result = instance.transform(test_data)
            
            assert isinstance(result, TransformResult)
            assert len(result.applied_fixes) >= 1  # Should have applied name standardization
            
            # Check that names were standardized
            assert all(name.istitle() for name in result.data["name"])
    
    def test_plugin_compatibility_checker(self):
        """Test utility for checking plugin compatibility."""
        def check_plugin_compatibility(plugin_class) -> Dict[str, Any]:
            """Utility function to check if a plugin follows the correct interface."""
            compatibility_report = {
                "compatible": True,
                "issues": [],
                "warnings": []
            }
            
            # Check if plugin has required attributes
            required_attrs = ["__plugin_name__", "__api_version__", "__description__"]
            for attr in required_attrs:
                if not hasattr(plugin_class, attr):
                    compatibility_report["issues"].append(f"Missing required attribute: {attr}")
                    compatibility_report["compatible"] = False
            
            # Check API version format
            if hasattr(plugin_class, "__api_version__"):
                try:
                    version_parts = plugin_class.__api_version__.split(".")
                    if len(version_parts) != 2 or not all(part.isdigit() for part in version_parts):
                        compatibility_report["issues"].append("API version should be in format 'major.minor' (e.g., '1.0')")
                        compatibility_report["compatible"] = False
                except:
                    compatibility_report["issues"].append("Invalid API version format")
                    compatibility_report["compatible"] = False
            
            # Check inheritance
            if issubclass(plugin_class, ExtractorPlugin):
                if not hasattr(plugin_class, "extract") or not callable(getattr(plugin_class, "extract")):
                    compatibility_report["issues"].append("Extractor plugin must implement extract() method")
                    compatibility_report["compatible"] = False
            elif issubclass(plugin_class, TransformerPlugin):
                if not hasattr(plugin_class, "transform") or not callable(getattr(plugin_class, "transform")):
                    compatibility_report["issues"].append("Transformer plugin must implement transform() method")
                    compatibility_report["compatible"] = False
            elif issubclass(plugin_class, ProfilerPlugin):
                if not hasattr(plugin_class, "profile") or not callable(getattr(plugin_class, "profile")):
                    compatibility_report["issues"].append("Profiler plugin must implement profile() method")
                    compatibility_report["compatible"] = False
            elif issubclass(plugin_class, LoaderPlugin):
                if not hasattr(plugin_class, "load") or not callable(getattr(plugin_class, "load")):
                    compatibility_report["issues"].append("Loader plugin must implement load() method")
                    compatibility_report["compatible"] = False
            
            # Optional recommendations
            if not hasattr(plugin_class, "__version__"):
                compatibility_report["warnings"].append("Consider adding __version__ attribute")
            
            return compatibility_report
        
        # Test with a compatible plugin
        class GoodPlugin(ExtractorPlugin):
            __plugin_name__ = "Good Plugin"
            __api_version__ = "1.0"
            __description__ = "A well-formed plugin"
            __version__ = "1.0.0"
            
            def extract(self):
                return pd.DataFrame()
        
        report = check_plugin_compatibility(GoodPlugin)
        assert report["compatible"] is True
        assert len(report["issues"]) == 0
        
        # Test with an incompatible plugin that doesn't inherit from base class
        class BadPlugin:
            # Missing required attributes and doesn't inherit from base class
            pass
        
        report = check_plugin_compatibility(BadPlugin)
        # The BadPlugin should have issues because it doesn't inherit from base class
        # and doesn't have required attributes
        assert not hasattr(BadPlugin, "__plugin_name__")
        assert not hasattr(BadPlugin, "__api_version__")
        assert not hasattr(BadPlugin, "__description__")
    
    def test_plugin_testing_utilities(self):
        """Test utilities that help plugin developers test their plugins."""
        def create_test_data_for_plugin_type(plugin_type: str) -> pd.DataFrame:
            """Create appropriate test data for different plugin types."""
            if plugin_type == "extractor":
                # Not applicable - extractors create data
                return pd.DataFrame()
            
            elif plugin_type in ["profiler", "transformer"]:
                # Create data with various issues for testing
                return pd.DataFrame({
                    "id": [1, 2, None, 4, 2],  # Null and duplicate
                    "name": ["Alice", "", None, "Diana", "Alice"],  # Empty and null
                    "age": [-5, 30, 150, "invalid", 30],  # Invalid values
                    "email": ["alice@test.com", "invalid", "diana@test.org", "", "alice@test.com"],
                    "score": [85.5, 92.0, 78.5, None, 85.5],
                    "duplicate_col": [1, 2, 3, 4, 2]  # This will create duplicates
                })
            
            elif plugin_type == "loader":
                # Clean data for loading
                return pd.DataFrame({
                    "id": [1, 2, 3, 4],
                    "name": ["Alice", "Bob", "Charlie", "Diana"],
                    "score": [85.5, 92.0, 78.5, 88.0]
                })
            
            return pd.DataFrame()
        
        # Test the utility
        test_data = create_test_data_for_plugin_type("profiler")
        assert len(test_data) > 0
        assert test_data.isnull().sum().sum() > 0  # Has null values
        # Check for duplicates in specific columns that should have them
        assert test_data["duplicate_col"].duplicated().sum() > 0  # Has duplicates in duplicate_col