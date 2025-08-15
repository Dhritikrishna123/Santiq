"""Tests for plugin manager."""

import pytest

from santiq.core.exceptions import PluginNotFoundError
from santiq.core.plugin_manager import PluginManager
from santiq.plugins.extractors.csv_extractor import CSVExtractor, ExtractorPlugin


def test_plugin_discovery(plugin_manager: PluginManager) -> None:
    """Test plugin discovery mechanism."""
    plugins = plugin_manager.discover_plugins()
    
    assert "extractor" in plugins
    assert "profiler" in plugins
    assert "transformer" in plugins
    assert "loader" in plugins
    
    # Should find at least the built-in CSV extractor
    extractor_names = [p["name"] for p in plugins["extractor"]]
    assert "csv_extractor" in extractor_names


def test_load_plugin(plugin_manager: PluginManager) -> None:
    """Test loading a specific plugin."""
    plugin_class = plugin_manager.load_plugin("csv_extractor", "extractor")
    assert plugin_class == CSVExtractor
    assert issubclass(plugin_class, ExtractorPlugin)


def test_load_nonexistent_plugin(plugin_manager: PluginManager) -> None:
    """Test loading a plugin that doesn't exist."""
    with pytest.raises(PluginNotFoundError):
        plugin_manager.load_plugin("nonexistent_plugin", "extractor")


def test_create_plugin_instance(plugin_manager: PluginManager, temp_dir) -> None:
    """Test creating a plugin instance."""
    config = {"path": str(temp_dir / "test.csv")}
    instance = plugin_manager.create_plugin_instance("csv_extractor", "extractor", config)
    
    assert isinstance(instance, CSVExtractor)
    assert instance.config == config