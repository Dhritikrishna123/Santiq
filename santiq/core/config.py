"""Configuration management for the Santiq platform."""

# Re-export the main classes and models for backward compatibility
from santiq.core.config_manager import ConfigManager
from santiq.core.config_models import PipelineConfig, PluginConfig

__all__ = ["ConfigManager", "PipelineConfig", "PluginConfig"]
