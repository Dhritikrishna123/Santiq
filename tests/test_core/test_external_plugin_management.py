"""Tests for external plugin management functionality."""

import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import yaml

from santiq.core.plugin_manager import PluginManager
from santiq.core.engine import ETLEngine


class TestExternalPluginConfiguration:
    """Test external plugin configuration loading and management."""
    
    def test_load_external_plugin_config(self, temp_dir: Path):
        """Test loading external plugin configuration from file."""
        # Create external plugin config
        config_dir = temp_dir / ".santiq"
        config_dir.mkdir()
        config_file = config_dir / "external_plugins.yml"
        
        config_data = {
            "plugins": {
                "test_extractor": {
                    "package": "test-package",
                    "type": "extractor",
                    "description": "Test extractor",
                    "version": "1.0.0",
                    "api_version": "1.0"
                }
            }
        }
        
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)
        
        # Test plugin manager with config
        plugin_manager = PluginManager(external_plugin_config=str(config_file))
        
        # Check if external plugin was loaded
        external_plugins = plugin_manager.list_external_plugins()
        assert "extractor" in external_plugins
        assert len(external_plugins["extractor"]) == 1
        
        plugin_info = external_plugins["extractor"][0]
        assert plugin_info["name"] == "test_extractor"
        assert plugin_info["package"] == "test-package"
        assert plugin_info["type"] == "extractor"
        assert plugin_info["source"] == "external"
    
    def test_add_external_plugin_config(self, temp_dir: Path):
        """Test adding external plugin configuration."""
        # Create a unique config file for this test
        config_file = temp_dir / "test_config.yml"
        plugin_manager = PluginManager(external_plugin_config=str(config_file))
        
        plugin_config = {
            "package": "new-package",
            "type": "loader",
            "description": "New loader plugin",
            "version": "2.0.0",
            "api_version": "1.0"
        }
        
        plugin_manager.add_external_plugin_config("new_loader", plugin_config)
        
        # Verify plugin was added
        external_plugins = plugin_manager.list_external_plugins()
        assert "loader" in external_plugins
        assert len(external_plugins["loader"]) == 1
        
        plugin_info = external_plugins["loader"][0]
        assert plugin_info["name"] == "new_loader"
        assert plugin_info["package"] == "new-package"
        assert plugin_info["type"] == "loader"
    
    def test_remove_external_plugin_config(self, temp_dir: Path):
        """Test removing external plugin configuration."""
        # Create a unique config file for this test
        config_file = temp_dir / "test_config.yml"
        plugin_manager = PluginManager(external_plugin_config=str(config_file))
        
        # Add plugin first
        plugin_config = {
            "package": "test-package",
            "type": "profiler",
            "description": "Test profiler"
        }
        
        plugin_manager.add_external_plugin_config("test_profiler", plugin_config)
        
        # Verify it was added
        external_plugins = plugin_manager.list_external_plugins()
        assert "profiler" in external_plugins
        assert len(external_plugins["profiler"]) == 1
        
        # Remove plugin
        plugin_manager.remove_external_plugin_config("test_profiler")
        
        # Verify it was removed
        external_plugins = plugin_manager.list_external_plugins()
        assert "profiler" not in external_plugins or len(external_plugins["profiler"]) == 0
    
    def test_get_external_plugin_info(self, temp_dir: Path):
        """Test getting external plugin information."""
        # Create a unique config file for this test
        config_file = temp_dir / "test_config.yml"
        plugin_manager = PluginManager(external_plugin_config=str(config_file))
        
        plugin_config = {
            "package": "info-package",
            "type": "extractor",
            "description": "Info extractor",
            "version": "1.5.0"
        }
        
        plugin_manager.add_external_plugin_config("info_extractor", plugin_config)
        
        # Get plugin info
        plugin_info = plugin_manager.get_external_plugin_info("info_extractor")
        assert plugin_info is not None
        assert plugin_info["package"] == "info-package"
        assert plugin_info["type"] == "extractor"
        assert plugin_info["version"] == "1.5.0"
        
        # Test non-existent plugin
        non_existent = plugin_manager.get_external_plugin_info("non_existent")
        assert non_existent is None


class TestExternalPluginDiscovery:
    """Test external plugin discovery and integration."""
    
    def test_discover_plugins_includes_external(self, temp_dir: Path):
        """Test that external plugins are included in plugin discovery."""
        # Create external plugin config
        config_dir = temp_dir / ".santiq"
        config_dir.mkdir()
        config_file = config_dir / "external_plugins.yml"
        
        config_data = {
            "plugins": {
                "external_extractor": {
                    "package": "external-package",
                    "type": "extractor",
                    "description": "External extractor"
                }
            }
        }
        
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)
        
        # Test plugin discovery
        plugin_manager = PluginManager(external_plugin_config=str(config_file))
        all_plugins = plugin_manager.discover_plugins()
        
        # Check that external plugin is included
        assert "extractor" in all_plugins
        extractor_plugins = all_plugins["extractor"]
        
        # Should include built-in plugins and external plugins
        external_plugin = next(
            (p for p in extractor_plugins if p["name"] == "external_extractor"), 
            None
        )
        assert external_plugin is not None
        assert external_plugin["source"] == "external"
    
    def test_external_plugin_installation_status(self, temp_dir: Path):
        """Test tracking of external plugin installation status."""
        # Create a unique config file for this test
        config_file = temp_dir / "test_config.yml"
        plugin_manager = PluginManager(external_plugin_config=str(config_file))
        
        # Add external plugin config
        plugin_config = {
            "package": "installed-package",
            "type": "transformer",
            "description": "Installed transformer"
        }
        
        plugin_manager.add_external_plugin_config("installed_transformer", plugin_config)
        
        # Mock package installation check
        with patch.object(plugin_manager, '_is_package_installed') as mock_installed:
            mock_installed.return_value = True
            
            external_plugins = plugin_manager.list_external_plugins()
            assert "transformer" in external_plugins
            
            plugin_info = external_plugins["transformer"][0]
            assert plugin_info["installed"] is True
            
            # Test with not installed package
            mock_installed.return_value = False
            
            external_plugins = plugin_manager.list_external_plugins()
            plugin_info = external_plugins["transformer"][0]
            assert plugin_info["installed"] is False


class TestETLEngineIntegration:
    """Test ETLEngine integration with external plugins."""
    
    def test_engine_external_plugin_methods(self, temp_dir: Path):
        """Test ETLEngine methods for external plugin management."""
        # Create a unique config file for this test
        config_file = temp_dir / "test_config.yml"
        engine = ETLEngine(external_plugin_config=str(config_file))
        
        # Test adding external plugin config
        plugin_config = {
            "package": "engine-package",
            "type": "loader",
            "description": "Engine loader"
        }
        
        engine.add_external_plugin_config("engine_loader", plugin_config)
        
        # Test listing external plugins
        external_plugins = engine.list_external_plugins()
        assert "loader" in external_plugins
        assert len(external_plugins["loader"]) == 1
        
        plugin_info = external_plugins["loader"][0]
        assert plugin_info["name"] == "engine_loader"
        assert plugin_info["package"] == "engine-package"
        assert plugin_info["type"] == "loader"
        
        # Test getting external plugin info
        plugin_info = engine.get_external_plugin_info("engine_loader")
        assert plugin_info is not None
        assert plugin_info["package"] == "engine-package"
        
        # Test removing external plugin config
        engine.remove_external_plugin_config("engine_loader")
        
        external_plugins = engine.list_external_plugins()
        assert "loader" not in external_plugins or len(external_plugins["loader"]) == 0


class TestExternalPluginCLI:
    """Test CLI integration with external plugins."""
    
    def test_cli_external_plugin_commands(self):
        """Test that CLI commands are properly registered."""
        from santiq.cli.commands.plugin import plugin_app
        
        # Check that external command is registered
        commands = [cmd.name for cmd in plugin_app.registered_commands]
        assert "external" in commands


class TestExternalPluginValidation:
    """Test external plugin configuration validation."""
    
    def test_invalid_plugin_type(self, temp_dir: Path):
        """Test handling of invalid plugin types."""
        # Create a unique config file for this test
        config_file = temp_dir / "test_config.yml"
        plugin_manager = PluginManager(external_plugin_config=str(config_file))
        
        # Add plugin with invalid type
        invalid_config = {
            "package": "invalid-package",
            "type": "invalid_type",
            "description": "Invalid plugin"
        }
        
        plugin_manager.add_external_plugin_config("invalid_plugin", invalid_config)
        
        # Plugin should be ignored during discovery
        external_plugins = plugin_manager.list_external_plugins()
        
        # Check that invalid plugin is not included
        for plugin_type, plugins in external_plugins.items():
            for plugin in plugins:
                assert plugin["name"] != "invalid_plugin"
    
    def test_missing_required_fields(self, temp_dir: Path):
        """Test handling of missing required fields."""
        # Create a unique config file for this test
        config_file = temp_dir / "test_config.yml"
        plugin_manager = PluginManager(external_plugin_config=str(config_file))
        
        # Add plugin with missing package
        incomplete_config = {
            "type": "extractor",
            "description": "Incomplete plugin"
        }
        
        plugin_manager.add_external_plugin_config("incomplete_plugin", incomplete_config)
        
        # Plugin should still be added but may not work properly
        external_plugins = plugin_manager.list_external_plugins()
        assert "extractor" in external_plugins
        
        # Find the incomplete plugin
        incomplete_plugin = next(
            (p for p in external_plugins["extractor"] if p["name"] == "incomplete_plugin"),
            None
        )
        assert incomplete_plugin is not None
        assert incomplete_plugin.get("package") is None
