"""Plugin discovery functionality for Santiq.

This module provides classes for discovering plugins from various sources:
- Entry points: Built-in and installed plugins from PyPI
- Local directories: Custom plugins in local directories
- Validation: Plugin validation and compatibility checking
"""

from santiq.core.discovery.entry_point_discovery import EntryPointDiscovery
from santiq.core.discovery.local_discovery import LocalDiscovery
from santiq.core.discovery.plugin_discovery import PluginDiscovery
from santiq.core.discovery.plugin_validator import PluginValidator

__all__ = [
    "PluginDiscovery",
    "EntryPointDiscovery",
    "LocalDiscovery",
    "PluginValidator",
]
