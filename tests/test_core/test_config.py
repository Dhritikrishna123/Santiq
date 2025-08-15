"""Tests for configuration management."""

import pytest
import os
import tempfile
from pathlib import Path
import yaml

from santiq.core.config import ConfigManager, PipelineConfig, PluginConfig
from santiq.core.exceptions import PipelineConfigError


class TestConfigManager:
    """Test configuration manager functionality."""
    
    def test_load_valid_config(self, temp_dir: Path):
        """Test loading a valid pipeline configuration."""
        config_data = {
            "name": "test_pipeline",
            "description": "A test pipeline",
            "extractor": {
                "plugin": "csv_extractor",
                "params": {"path": "/test/input.csv"}
            },
            "loaders": [{
                "plugin": "csv_loader",
                "params": {"path": "/test/output.csv"}
            }]
        }
        
        config_file = temp_dir / "config.yml"
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)
        
        config_manager = ConfigManager()
        pipeline_config = config_manager.load_pipeline_config(str(config_file))
        
        assert isinstance(pipeline_config, PipelineConfig)
        assert pipeline_config.name == "test_pipeline"
        assert pipeline_config.extractor.plugin == "csv_extractor"
        assert len(pipeline_config.loaders) == 1
    
    def test_load_nonexistent_config(self, config_manager: ConfigManager):
        """Test loading a non-existent configuration file."""
        with pytest.raises(PipelineConfigError) as exc_info:
            config_manager.load_pipeline_config("/nonexistent/config.yml")
        
        assert "not found" in str(exc_info.value)
    
    def test_load_invalid_yaml(self, temp_dir: Path, config_manager: ConfigManager):
        """Test loading invalid YAML."""
        config_file = temp_dir / "invalid.yml"
        config_file.write_text("invalid: yaml: content: [")
        
        with pytest.raises(PipelineConfigError) as exc_info:
            config_manager.load_pipeline_config(str(config_file))
        
        assert "Invalid YAML" in str(exc_info.value)
    
    def test_environment_variable_substitution(self, temp_dir: Path):
        """Test environment variable substitution."""
        # Set environment variables
        os.environ["TEST_INPUT_PATH"] = "/test/input"
        os.environ["TEST_OUTPUT_PATH"] = "/test/output"
        
        try:
            config_data = {
                "extractor": {
                    "plugin": "csv_extractor",
                    "params": {"path": "${TEST_INPUT_PATH}/data.csv"}
                },
                "loaders": [{
                    "plugin": "csv_loader", 
                    "params": {"path": "${TEST_OUTPUT_PATH}/result.csv"}
                }]
            }
            
            config_file = temp_dir / "config.yml"
            with open(config_file, 'w') as f:
                yaml.dump(config_data, f)
            
            config_manager = ConfigManager()
            pipeline_config = config_manager.load_pipeline_config(str(config_file))
            
            assert pipeline_config.extractor.params["path"] == "/test/input/data.csv"
            assert pipeline_config.loaders[0].params["path"] == "/test/output/result.csv"
            
        finally:
            # Clean up environment variables
            os.environ.pop("TEST_INPUT_PATH", None)
            os.environ.pop("TEST_OUTPUT_PATH", None)
    
    def test_env_var_with_defaults(self, temp_dir: Path):
        """Test environment variable substitution with defaults."""
        config_data = {
            "extractor": {
                "plugin": "csv_extractor",
                "params": {"path": "${UNDEFINED_VAR:/default/path}/data.csv"}
            },
            "loaders": [{"plugin": "csv_loader", "params": {"path": "/output.csv"}}]
        }
        
        config_file = temp_dir / "config.yml"
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)
        
        config_manager = ConfigManager()
        pipeline_config = config_manager.load_pipeline_config(str(config_file))
        
        assert pipeline_config.extractor.params["path"] == "/default/path/data.csv"


class TestPipelineConfig:
    """Test pipeline configuration validation."""
    
    def test_valid_minimal_config(self):
        """Test valid minimal configuration."""
        config_data = {
            "extractor": {
                "plugin": "csv_extractor",
                "params": {"path": "/input.csv"}
            },
            "loaders": [{
                "plugin": "csv_loader",
                "params": {"path": "/output.csv"}
            }]
        }
        
        config = PipelineConfig(**config_data)
        assert config.extractor.plugin == "csv_extractor"
        assert len(config.loaders) == 1
        assert len(config.profilers) == 0
        assert len(config.transformers) == 0
    
    def test_config_without_loaders(self):
        """Test configuration validation fails without loaders."""
        config_data = {
            "extractor": {
                "plugin": "csv_extractor", 
                "params": {"path": "/input.csv"}
            },
            "loaders": []  # Empty loaders should fail
        }
        
        with pytest.raises(ValueError) as exc_info:
            PipelineConfig(**config_data)
        
        assert "At least one loader must be specified" in str(exc_info.value)
    
    def test_plugin_config_defaults(self):
        """Test plugin configuration defaults."""
        plugin_config = PluginConfig(plugin="test_plugin")
        
        assert plugin_config.plugin == "test_plugin"
        assert plugin_config.params == {}
        assert plugin_config.on_error == "stop"
        assert plugin_config.enabled is True
