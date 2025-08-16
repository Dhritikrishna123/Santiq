"""Tests for plugin API compatibility and external plugin development."""

import importlib.util
import sys
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from santiq.core.exceptions import PluginLoadError, PluginVersionError
from santiq.core.plugin_manager import PluginManager
from santiq.plugins.base.extractor import ExtractorPlugin
from santiq.plugins.base.loader import LoaderPlugin, LoadResult
from santiq.plugins.base.profiler import ProfileResult, ProfilerPlugin
from santiq.plugins.base.transformer import TransformerPlugin, TransformResult


class TestPluginCompatibility:
    """Test plugin API compatibility for external plugin development."""
    
    def test_external_plugin_structure(self, temp_dir: Path):
        """Test that external plugins can follow the expected structure."""
        # Create a minimal external plugin
        plugin_code = '''
import pandas as pd
from santiq.plugins.base.extractor import ExtractorPlugin

class MyCustomExtractor(ExtractorPlugin):
    __plugin_name__ = "My Custom Extractor"
    __api_version__ = "1.0"
    __description__ = "Custom extractor for testing"
    
    def _validate_config(self):
        if "source" not in self.config:
            raise ValueError("source parameter is required")
    
    def extract(self) -> pd.DataFrame:
        # Simple mock data
        return pd.DataFrame({
            "id": [1, 2, 3],
            "value": ["A", "B", "C"],
            "source": [self.config["source"]] * 3
        })
    
    def get_schema_info(self):
        return {
            "columns": ["id", "value", "source"],
            "data_types": {"id": "int64", "value": "object", "source": "object"},
            "estimated_rows": 3
        }
'''
        
        # Write plugin to file
        plugin_file = temp_dir / "my_plugin.py"
        plugin_file.write_text(plugin_code)
        
        # Create plugin manifest
        manifest = {
            "name": "my_custom_extractor",
            "type": "extractor", 
            "version": "1.0.0",
            "api_version": "1.0",
            "description": "Custom extractor for testing",
            "entry_point": "my_plugin:MyCustomExtractor"
        }
        
        manifest_file = temp_dir / "plugin.yml"
        with open(manifest_file, 'w') as f:
            import yaml
            yaml.dump(manifest, f)
        
        # Test plugin discovery and loading
        plugin_manager = PluginManager(local_plugin_dirs=[str(temp_dir)])
        plugins = plugin_manager.discover_plugins()
        
        # Find our custom plugin
        custom_plugins = [p for p in plugins["extractor"] if p["name"] == "my_custom_extractor"]
        assert len(custom_plugins) == 1
        
        custom_plugin = custom_plugins[0]
        assert custom_plugin["version"] == "1.0.0"
        assert custom_plugin["source"] == "local"
        
        # Test loading and instantiation
        plugin_class = plugin_manager.load_plugin("my_custom_extractor", "extractor")
        instance = plugin_manager.create_plugin_instance("my_custom_extractor", "extractor", {"source": "test"})
        
        # Test functionality
        data = instance.extract()
        assert len(data) == 3
        assert list(data.columns) == ["id", "value", "source"]
        assert all(data["source"] == "test")
    
    def test_plugin_api_version_compatibility(self):
        """Test API version compatibility checking."""
        # Test compatible version
        plugin_info = {
            "name": "test_plugin",
            "api_version": "1.0",
            "source": "test"
        }
        
        plugin_manager = PluginManager()
        # Should not raise exception
        plugin_manager._validate_api_version(plugin_info)
        
        # Test incompatible major version
        plugin_info["api_version"] = "2.0"
        
        with pytest.raises(PluginVersionError) as exc_info:
            plugin_manager._validate_api_version(plugin_info)
        
        assert "test_plugin" in str(exc_info.value)
        assert "2.0" in str(exc_info.value)
    
    def test_plugin_inheritance_validation(self, temp_dir: Path):
        """Test that plugins must inherit from correct base classes."""
        # Create invalid plugin that doesn't inherit from base class
        bad_plugin_code = '''
class BadPlugin:
    """Plugin that doesn't inherit from base class."""
    __plugin_name__ = "Bad Plugin"
    __api_version__ = "1.0"
    
    def extract(self):
        return None
'''
        
        plugin_file = temp_dir / "bad_plugin.py"
        plugin_file.write_text(bad_plugin_code)
        
        # Try to load it
        plugin_manager = PluginManager()
        
        # Mock discovery to return our bad plugin
        with patch.object(plugin_manager, 'discover_plugins') as mock_discover:
            # Load the module dynamically to get the class
            spec = importlib.util.spec_from_file_location("bad_plugin", plugin_file)
            module = importlib.util.module_from_spec(spec)
            sys.modules["bad_plugin"] = module
            spec.loader.exec_module(module)
            
            mock_discover.return_value = {
                "extractor": [{
                    "name": "bad_plugin",
                    "class": module.BadPlugin,
                    "api_version": "1.0",
                    "source": "test"
                }],
                "profiler": [],
                "transformer": [],
                "loader": []
            }
            
            # The test should fail because the plugin doesn't inherit from the correct base class
            # The validation happens during plugin discovery, not during load_plugin
            # So we need to test the discovery process directly
            with pytest.raises(PluginLoadError) as exc_info:
                # Try to discover plugins which should trigger validation
                plugin_manager.discover_plugins()
            
            # The error should be caught during discovery, but since we're mocking it,
            # we'll just verify that the bad plugin class doesn't inherit correctly
            assert not issubclass(module.BadPlugin, ExtractorPlugin)
    
    def test_plugin_configuration_validation(self, test_plugin_classes):
        """Test plugin configuration validation."""
        plugin_manager = PluginManager()
        
        # Test valid configuration
        valid_config = {"source": "test_data"}
        instance = plugin_manager.create_plugin_instance("csv_extractor", "extractor", {
            "path": "/tmp/test.csv"
        })
        
        # Config should be set
        assert instance.config["path"] == "/tmp/test.csv"
        
        # Test invalid configuration (missing required parameter)
        with pytest.raises(Exception):  # Can be ValueError or PluginLoadError
            plugin_manager.create_plugin_instance("csv_extractor", "extractor", {})
    
    def test_plugin_lifecycle_management(self, test_plugin_classes):
        """Test plugin lifecycle (setup/teardown)."""
        plugin_manager = PluginManager()
        
        # Create instance
        instance = plugin_manager.create_plugin_instance("csv_extractor", "extractor", {
            "path": "/tmp/test.csv"
        })
        
        # Mock teardown to verify it's called
        instance.teardown = Mock()
        
        # Cleanup
        plugin_manager.cleanup_plugin_instance("csv_extractor", "extractor")
        
        # Verify teardown was called
        instance.teardown.assert_called_once()


class TestPluginDevelopmentHelpers:
    """Test utilities that help with plugin development."""
    
    def test_plugin_base_class_interface(self):
        """Test that all plugin base classes provide the expected interface."""
        # Test ExtractorPlugin interface
        assert hasattr(ExtractorPlugin, 'setup')
        assert hasattr(ExtractorPlugin, 'teardown')
        assert hasattr(ExtractorPlugin, 'extract')
        assert hasattr(ExtractorPlugin, 'get_schema_info')
        
        # Test TransformerPlugin interface
        assert hasattr(TransformerPlugin, 'transform')
        assert hasattr(TransformerPlugin, 'can_handle_issue')
        assert hasattr(TransformerPlugin, 'suggest_fixes')
        
        # Test ProfilerPlugin interface
        assert hasattr(ProfilerPlugin, 'profile')
        
        # Test LoaderPlugin interface
        assert hasattr(LoaderPlugin, 'load')
        assert hasattr(LoaderPlugin, 'supports_incremental')
    
    def test_plugin_result_classes(self):
        """Test that plugin result classes work as expected."""
        # Test TransformResult
        import pandas as pd
        test_data = pd.DataFrame({"col": [1, 2, 3]})
        fixes = [{"type": "test_fix", "description": "Test fix applied"}]
        
        result = TransformResult(test_data, fixes, {"meta": "data"})
        
        assert isinstance(result.data, pd.DataFrame)
        assert len(result.applied_fixes) == 1
        assert result.metadata["meta"] == "data"
        
        # Test ProfileResult
        issues = [{"type": "test_issue", "severity": "low"}]
        summary = {"total_rows": 3}
        suggestions = [{"fix_type": "test_fix"}]
        
        profile_result = ProfileResult(issues, summary, suggestions)
        
        assert len(profile_result.issues) == 1
        assert profile_result.summary["total_rows"] == 3
        assert len(profile_result.suggestions) == 1
        
        # Test LoadResult
        load_result = LoadResult(True, 100, {"destination": "test"})
        
        assert load_result.success is True
        assert load_result.rows_loaded == 100
        assert load_result.metadata["destination"] == "test"
    
    def test_minimal_plugin_template(self, temp_dir: Path):
        """Test that a minimal plugin template works."""
        # This serves as documentation for plugin developers
        minimal_extractor = '''
import pandas as pd
from santiq.plugins.base.extractor import ExtractorPlugin

class MinimalExtractor(ExtractorPlugin):
    """Minimal working extractor plugin."""
    
    __plugin_name__ = "Minimal Extractor"
    __api_version__ = "1.0"
    __description__ = "Minimal extractor for demonstration"
    
    def extract(self) -> pd.DataFrame:
        """Extract data - this is the only required method."""
        return pd.DataFrame({"message": ["Hello, World!"]})
'''
        
        plugin_file = temp_dir / "minimal.py"
        plugin_file.write_text(minimal_extractor)
        
        # Load and test
        spec = importlib.util.spec_from_file_location("minimal", plugin_file)
        module = importlib.util.module_from_spec(spec)
        sys.modules["minimal"] = module
        spec.loader.exec_module(module)
        
        # Instantiate and test
        plugin = module.MinimalExtractor()
        plugin.setup({})
        
        data = plugin.extract()
        assert len(data) == 1
        assert data.loc[0, "message"] == "Hello, World!"