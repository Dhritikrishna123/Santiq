"""Tests for plugin manager functionality."""

import pytest
from unittest.mock import Mock, patch, mock_open
import importlib.metadata
from pathlib import Path

from santiq.core.exceptions import PluginNotFoundError, PluginLoadError, PluginVersionError
from santiq.core.plugin_manager import PluginManager
from santiq.plugins.extractors.csv_extractor import CSVExtractor
from santiq.plugins.base.extractor import ExtractorPlugin


class TestPluginDiscovery:
    """Test plugin discovery mechanisms."""
    
    def test_discover_builtin_plugins(self, plugin_manager: PluginManager):
        """Test discovery of built-in plugins."""
        plugins = plugin_manager.discover_plugins()
        
        assert "extractor" in plugins
        assert "profiler" in plugins
        assert "transformer" in plugins
        assert "loader" in plugins
        
        # Should find built-in CSV extractor
        extractor_names = [p["name"] for p in plugins["extractor"]]
        assert "csv_extractor" in extractor_names
    
    def test_discover_local_plugins(self, temp_dir: Path):
        """Test discovery of local plugins."""
        # Create a mock local plugin
        plugin_dir = temp_dir / "test_plugin"
        plugin_dir.mkdir()
        
        manifest = {
            "name": "test_local_plugin",
            "type": "extractor", 
            "version": "1.0.0",
            "api_version": "1.0",
            "description": "Test local plugin",
            "entry_point": "test_plugin:TestPlugin"
        }
        
        (plugin_dir / "plugin.yml").write_text(
            "name: test_local_plugin\n"
            "type: extractor\n"
            "version: 1.0.0\n"
            "api_version: '1.0'\n"
            "description: Test local plugin\n"
            "entry_point: test_plugin:TestPlugin\n"
        )
        
        # Create mock plugin file
        (plugin_dir / "test_plugin.py").write_text(
            "from santiq.plugins.base.extractor import ExtractorPlugin\n"
            "import pandas as pd\n"
            "class TestPlugin(ExtractorPlugin):\n"
            "    def extract(self):\n"
            "        return pd.DataFrame({'test': [1,2,3]})\n"
        )
        
        plugin_manager = PluginManager(local_plugin_dirs=[str(temp_dir)])
        plugins = plugin_manager.discover_plugins()
        
        local_plugins = [p for p in plugins["extractor"] if p.get("source") == "local"]
        assert len(local_plugins) >= 1
        
        local_plugin = next(p for p in local_plugins if p["name"] == "test_local_plugin")
        assert local_plugin["version"] == "1.0.0"
        assert local_plugin["description"] == "Test local plugin"


class TestPluginLoading:
    """Test plugin loading functionality."""
    
    def test_load_builtin_plugin(self, plugin_manager: PluginManager):
        """Test loading a built-in plugin."""
        plugin_class = plugin_manager.load_plugin("csv_extractor", "extractor")
        assert plugin_class == CSVExtractor
        assert issubclass(plugin_class, ExtractorPlugin)
    
    def test_load_nonexistent_plugin(self, plugin_manager: PluginManager):
        """Test loading a plugin that doesn't exist."""
        with pytest.raises(PluginNotFoundError) as exc_info:
            plugin_manager.load_plugin("nonexistent_plugin", "extractor")
        
        assert "nonexistent_plugin" in str(exc_info.value)
        assert "extractor" in str(exc_info.value)
    
    def test_load_plugin_invalid_type(self, plugin_manager: PluginManager):
        """Test loading plugin with invalid type."""
        with pytest.raises(Exception) as exc_info:
            plugin_manager.load_plugin("csv_extractor", "invalid_type")
        
        assert "Unknown plugin type" in str(exc_info.value)
    
    def test_plugin_caching(self, plugin_manager: PluginManager):
        """Test that plugins are cached after first load."""
        plugin_class1 = plugin_manager.load_plugin("csv_extractor", "extractor")
        plugin_class2 = plugin_manager.load_plugin("csv_extractor", "extractor")
        
        assert plugin_class1 is plugin_class2  # Same object (cached)


class TestPluginInstantiation:
    """Test plugin instance creation and management."""
    
    def test_create_plugin_instance(self, plugin_manager: PluginManager, temp_dir: Path):
        """Test creating a plugin instance."""
        config = {"path": str(temp_dir / "test.csv")}
        instance = plugin_manager.create_plugin_instance("csv_extractor", "extractor", config)
        
        assert isinstance(instance, CSVExtractor)
        assert instance.config == config
    
    def test_plugin_instance_cleanup(self, plugin_manager: PluginManager, temp_dir: Path):
        """Test plugin instance cleanup."""
        config = {"path": str(temp_dir / "test.csv")}
        instance = plugin_manager.create_plugin_instance("csv_extractor", "extractor", config)
        
        # Mock the teardown method to verify it's called
        instance.teardown = Mock()
        
        plugin_manager.cleanup_plugin_instance("csv_extractor", "extractor")
        instance.teardown.assert_called_once()


class TestPluginCompatibility:
    """Test plugin API compatibility checking."""
    
    def test_api_version_validation(self, plugin_manager: PluginManager, test_plugin_classes):
        """Test API version compatibility validation."""
        # Mock discovery to return our test plugin
        with patch.object(plugin_manager, 'discover_plugins') as mock_discover:
            mock_discover.return_value = {
                "extractor": [{
                    "name": "incompatible_plugin",
                    "class": test_plugin_classes["incompatible_extractor"],
                    "api_version": "999.0",
                    "source": "test"
                }],
                "profiler": [],
                "transformer": [],
                "loader": []
            }
            
            with pytest.raises(PluginVersionError) as exc_info:
                plugin_manager.load_plugin("incompatible_plugin", "extractor")
            
            assert "incompatible_plugin" in str(exc_info.value)
            assert "999.0" in str(exc_info.value)

