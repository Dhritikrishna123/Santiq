"""Main plugin discovery orchestrator."""

from typing import Any, Dict, List

from santiq.core.discovery.entry_point_discovery import EntryPointDiscovery
from santiq.core.discovery.local_discovery import LocalDiscovery


class PluginDiscovery:
    """Orchestrates discovery of plugins from various sources.

    This class coordinates the discovery of plugins from:
    - Entry points: Built-in and installed plugins from PyPI
    - Local directories: Custom plugins in local directories

    It combines results from both discovery methods and provides
    a unified interface for plugin discovery.
    """

    def __init__(self, local_plugin_dirs: List[str] | None = None) -> None:
        """Initialize plugin discovery.

        Args:
            local_plugin_dirs: List of local directories to search for plugins
        """
        self.local_plugin_dirs = local_plugin_dirs or []
        self.entry_point_discovery = EntryPointDiscovery()
        self.local_discovery = LocalDiscovery()

    def discover_all_plugins(self) -> Dict[str, List[Dict[str, Any]]]:
        """Discover all available plugins from entry points and local directories.

        Returns:
            Dictionary mapping plugin types to lists of plugin information
        """
        # Discover entry point plugins (built-in and installed from PyPI)
        plugins = self.entry_point_discovery.discover_entry_point_plugins()

        # Discover local plugins
        local_plugins = self.local_discovery.discover_local_plugins(
            self.local_plugin_dirs
        )

        # Combine results
        for plugin_type, plugin_list in local_plugins.items():
            plugins[plugin_type].extend(plugin_list)

        return plugins
