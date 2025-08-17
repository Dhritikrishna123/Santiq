"""Plugin manager for discovering and loading Santiq plugins"""

from typing import Any, Dict, List, Optional, Type, Union

from santiq.core.exceptions import (
    PluginError,
    PluginLoadError,
    PluginNotFoundError,
    PluginVersionError,
)
from santiq.core.external_plugin_manager import ExternalPluginManager
from santiq.core.plugin_discovery import PluginDiscovery
from santiq.core.plugin_lifecycle import PluginLifecycleManager
from santiq.plugins.base.extractor import ExtractorPlugin
from santiq.plugins.base.loader import LoaderPlugin
from santiq.plugins.base.profiler import ProfilerPlugin
from santiq.plugins.base.transformer import TransformerPlugin

PluginType = Union[ExtractorPlugin, ProfilerPlugin, TransformerPlugin, LoaderPlugin]
PluginClass = Type[PluginType]


class PluginManager:
    """Manages plugin discovery, loading and lifecycle"""

    PLUGIN_TYPES = {
        "extractor": ExtractorPlugin,
        "profiler": ProfilerPlugin,
        "transformer": TransformerPlugin,
        "loader": LoaderPlugin,
    }

    def __init__(
        self,
        local_plugin_dirs: Optional[List[str]] = None,
        external_plugin_config: Optional[str] = None,
    ) -> None:
        """Initialize the plugin manager.

        Args:
            local_plugin_dirs: List of local directories to search for plugins
            external_plugin_config: Path to external plugin configuration file
        """
        self.discovery = PluginDiscovery(local_plugin_dirs)
        self.external_manager = ExternalPluginManager(external_plugin_config)
        self.lifecycle_manager = PluginLifecycleManager()

    def discover_plugins(self) -> Dict[str, List[Dict[str, Any]]]:
        """Discover all available plugins from entry points, local directories, and external config.

        Returns:
            Dictionary mapping plugin types to lists of plugin information
        """
        # Discover entry point and local plugins
        plugins = self.discovery.discover_all_plugins()

        # Discover external plugins from configuration
        external_plugins = self.external_manager.discover_external_plugins()
        for plugin_type, plugin_list in external_plugins.items():
            plugins[plugin_type].extend(plugin_list)

        return plugins

    def load_plugin(self, plugin_name: str, plugin_type: str) -> Type[PluginType]:
        """Load a specific plugin by name and type.

        Args:
            plugin_name: Name of the plugin to load
            plugin_type: Type of plugin (extractor, profiler, etc.)

        Returns:
            The loaded plugin class

        Raises:
            PluginError: If plugin type is unknown
            PluginNotFoundError: If plugin is not found
            PluginVersionError: If API version is incompatible
        """
        plugins = self.discover_plugins()
        return self.lifecycle_manager.load_plugin(plugin_name, plugin_type, plugins)

    def create_plugin_instance(
        self,
        plugin_name: str,
        plugin_type: str,
        config: Optional[Dict[str, Any]] = None,
    ) -> PluginType:
        """Create and configure a plugin instance.

        Args:
            plugin_name: Name of the plugin
            plugin_type: Type of plugin
            config: Configuration dictionary for the plugin

        Returns:
            Configured plugin instance
        """
        # Ensure plugin is loaded first
        self.load_plugin(plugin_name, plugin_type)
        return self.lifecycle_manager.create_plugin_instance(plugin_name, plugin_type, config)

    def get_plugin_instance(
        self, plugin_name: str, plugin_type: str
    ) -> Optional[PluginType]:
        """Get an existing plugin instance.

        Args:
            plugin_name: Name of the plugin
            plugin_type: Type of plugin

        Returns:
            Plugin instance if it exists, None otherwise
        """
        return self.lifecycle_manager.get_plugin_instance(plugin_name, plugin_type)

    def cleanup_plugin_instance(self, plugin_name: str, plugin_type: str) -> None:
        """Cleanup a plugin instance.

        Args:
            plugin_name: Name of the plugin
            plugin_type: Type of plugin
        """
        self.lifecycle_manager.cleanup_plugin_instance(plugin_name, plugin_type)

    def cleanup_all_instances(self) -> None:
        """Cleanup all plugin instances."""
        self.lifecycle_manager.cleanup_all_instances()

    def list_plugins(
        self, plugin_type: Optional[str] = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        """List all available plugins.

        Args:
            plugin_type: Specific plugin type to list, or None for all types

        Returns:
            Dictionary mapping plugin types to lists of plugin information

        Raises:
            PluginError: If specified plugin type is unknown
        """
        discovered = self.discover_plugins()

        if plugin_type:
            if plugin_type not in self.PLUGIN_TYPES:
                raise PluginError(f"Unknown plugin type: {plugin_type}")
            return {plugin_type: discovered[plugin_type]}

        return discovered

    def get_plugin_info(
        self, plugin_name: str, plugin_type: str
    ) -> Optional[Dict[str, Any]]:
        """Get information about a specific plugin.

        Args:
            plugin_name: Name of the plugin
            plugin_type: Type of plugin

        Returns:
            Plugin information dictionary if found, None otherwise
        """
        plugins = self.discover_plugins()

        for plugin_info in plugins.get(plugin_type, []):
            if plugin_info["name"] == plugin_name:
                return plugin_info

        return None

    def is_plugin_loaded(self, plugin_name: str, plugin_type: str) -> bool:
        """Check if a plugin is loaded.

        Args:
            plugin_name: Name of the plugin
            plugin_type: Type of plugin

        Returns:
            True if plugin is loaded, False otherwise
        """
        return self.lifecycle_manager.is_plugin_loaded(plugin_name, plugin_type)

    def unload_plugin(self, plugin_name: str, plugin_type: str) -> None:
        """Unload a plugin and cleanup its instances.

        Args:
            plugin_name: Name of the plugin
            plugin_type: Type of plugin
        """
        self.lifecycle_manager.unload_plugin(plugin_name, plugin_type)

    # External plugin management methods
    def install_external_plugin(
        self,
        plugin_name: str,
        package_name: Optional[str] = None,
        source: Optional[str] = None,
        upgrade: bool = False,
    ) -> bool:
        """Install an external plugin package.

        Args:
            plugin_name: Name of the plugin
            package_name: PyPI package name (if different from plugin name)
            source: Custom package index URL
            upgrade: Whether to upgrade if already installed

        Returns:
            True if installation successful, False otherwise
        """
        return self.external_manager.install_external_plugin(
            plugin_name, package_name, source, upgrade
        )

    def uninstall_external_plugin(
        self, plugin_name: str, package_name: Optional[str] = None
    ) -> bool:
        """Uninstall an external plugin package.

        Args:
            plugin_name: Name of the plugin
            package_name: PyPI package name (if different from plugin name)

        Returns:
            True if uninstallation successful, False otherwise
        """
        return self.external_manager.uninstall_external_plugin(plugin_name, package_name)

    def add_external_plugin_config(
        self, plugin_name: str, plugin_config: Dict[str, Any]
    ) -> None:
        """Add external plugin configuration.

        Args:
            plugin_name: Name of the plugin
            plugin_config: Plugin configuration dictionary
        """
        self.external_manager.add_external_plugin_config(plugin_name, plugin_config)

    def remove_external_plugin_config(self, plugin_name: str) -> None:
        """Remove external plugin configuration.

        Args:
            plugin_name: Name of the plugin to remove
        """
        self.external_manager.remove_external_plugin_config(plugin_name)

    def get_external_plugin_info(self, plugin_name: str) -> Optional[Dict[str, Any]]:
        """Get information about an external plugin.

        Args:
            plugin_name: Name of the plugin

        Returns:
            Plugin configuration if found, None otherwise
        """
        return self.external_manager.get_external_plugin_info(plugin_name)

    def list_external_plugins(self) -> Dict[str, List[Dict[str, Any]]]:
        """List all configured external plugins.

        Returns:
            Dictionary mapping plugin types to lists of external plugin information
        """
        return self.external_manager.list_external_plugins()
