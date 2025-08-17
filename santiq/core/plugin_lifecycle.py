"""Plugin lifecycle management functionality for Santiq."""

from typing import Any, Dict, Optional, Type

from packaging import version

from santiq.core.exceptions import (
    PluginError,
    PluginLoadError,
    PluginNotFoundError,
    PluginVersionError,
)
from santiq.plugins.base.extractor import ExtractorPlugin
from santiq.plugins.base.loader import LoaderPlugin
from santiq.plugins.base.profiler import ProfilerPlugin
from santiq.plugins.base.transformer import TransformerPlugin

PluginType = ExtractorPlugin | ProfilerPlugin | TransformerPlugin | LoaderPlugin
PluginClass = Type[PluginType]

PLUGIN_TYPES = {
    "extractor": ExtractorPlugin,
    "profiler": ProfilerPlugin,
    "transformer": TransformerPlugin,
    "loader": LoaderPlugin,
}


class PluginLifecycleManager:
    """Manages plugin loading, validation, and lifecycle."""

    def __init__(self) -> None:
        """Initialize plugin lifecycle manager."""
        self._loaded_plugins: Dict[str, Dict[str, PluginClass]] = {
            plugin_type: {} for plugin_type in PLUGIN_TYPES
        }
        self._plugin_instances: Dict[str, PluginType] = {}

    def load_plugin(
        self, plugin_name: str, plugin_type: str, plugins: Dict[str, list]
    ) -> PluginClass:
        """Load a specific plugin by name and type.

        Args:
            plugin_name: Name of the plugin to load
            plugin_type: Type of plugin (extractor, profiler, etc.)
            plugins: Dictionary of discovered plugins

        Returns:
            The loaded plugin class

        Raises:
            PluginError: If plugin type is unknown
            PluginNotFoundError: If plugin is not found
            PluginVersionError: If API version is incompatible
        """
        if plugin_type not in PLUGIN_TYPES:
            raise PluginError(f"Unknown plugin type: {plugin_type}")

        # Check if already loaded
        if plugin_name in self._loaded_plugins[plugin_type]:
            return self._loaded_plugins[plugin_type][plugin_name]

        # Find plugin in discovered plugins
        for plugin_info in plugins[plugin_type]:
            if plugin_info["name"] == plugin_name:
                # Validate API version
                self._validate_api_version(plugin_info)

                plugin_class = plugin_info["class"]
                self._loaded_plugins[plugin_type][plugin_name] = plugin_class
                return plugin_class

        raise PluginNotFoundError(plugin_name, plugin_type)

    def _validate_api_version(self, plugin_info: Dict[str, Any]) -> None:
        """Validate plugin API version compatibility.

        Args:
            plugin_info: Plugin information dictionary

        Raises:
            PluginVersionError: If API version is incompatible
        """
        plugin_api_version = plugin_info.get("api_version", "1.0")

        try:
            plugin_version_parsed = version.parse(plugin_api_version)

            # For now, accept any API version 1.x as compatible
            # This allows for future API evolution while maintaining compatibility
            if plugin_version_parsed.major != 1:
                raise PluginVersionError(plugin_info["name"], "1.x", plugin_api_version)

        except version.InvalidVersion as e:
            raise PluginVersionError(
                plugin_info["name"], "valid semantic version", plugin_api_version
            ) from e

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
        if (
            plugin_type not in self._loaded_plugins
            or plugin_name not in self._loaded_plugins[plugin_type]
        ):
            raise PluginNotFoundError(plugin_name, plugin_type)

        plugin_class = self._loaded_plugins[plugin_type][plugin_name]

        try:
            instance = plugin_class()

            # Setup with config if provided
            if config is not None:
                if hasattr(instance, "setup") and callable(instance.setup):
                    instance.setup(config)
                else:
                    print(f"Warning: Plugin {plugin_name} does not have a setup method")

            instance_key = f"{plugin_type}:{plugin_name}"
            self._plugin_instances[instance_key] = instance

            return instance

        except Exception as e:
            raise PluginLoadError(plugin_name, e)

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
        instance_key = f"{plugin_type}:{plugin_name}"
        return self._plugin_instances.get(instance_key)

    def cleanup_plugin_instance(self, plugin_name: str, plugin_type: str) -> None:
        """Cleanup a plugin instance.

        Args:
            plugin_name: Name of the plugin
            plugin_type: Type of plugin
        """
        instance_key = f"{plugin_type}:{plugin_name}"
        if instance_key in self._plugin_instances:
            instance = self._plugin_instances[instance_key]

            # Call teardown if available
            if hasattr(instance, "teardown") and callable(instance.teardown):
                try:
                    instance.teardown()
                except Exception as e:
                    print(f"Warning: Error during teardown of {plugin_name}: {e}")

            del self._plugin_instances[instance_key]

    def cleanup_all_instances(self) -> None:
        """Cleanup all plugin instances."""
        # Create a copy of keys to avoid dict changing during iteration
        instance_keys = list(self._plugin_instances.keys())

        for instance_key in instance_keys:
            plugin_type, plugin_name = instance_key.split(":", 1)
            self.cleanup_plugin_instance(plugin_name, plugin_type)

    def is_plugin_loaded(self, plugin_name: str, plugin_type: str) -> bool:
        """Check if a plugin is loaded.

        Args:
            plugin_name: Name of the plugin
            plugin_type: Type of plugin

        Returns:
            True if plugin is loaded, False otherwise
        """
        return plugin_name in self._loaded_plugins.get(plugin_type, {})

    def unload_plugin(self, plugin_name: str, plugin_type: str) -> None:
        """Unload a plugin and cleanup its instances.

        Args:
            plugin_name: Name of the plugin
            plugin_type: Type of plugin
        """
        # Cleanup any instances first
        self.cleanup_plugin_instance(plugin_name, plugin_type)

        # Remove from loaded plugins
        if plugin_type in self._loaded_plugins:
            self._loaded_plugins[plugin_type].pop(plugin_name, None)

    def get_loaded_plugins(self) -> Dict[str, Dict[str, PluginClass]]:
        """Get all loaded plugins.

        Returns:
            Dictionary of loaded plugins by type and name
        """
        return self._loaded_plugins.copy()

    def get_plugin_instances(self) -> Dict[str, PluginType]:
        """Get all plugin instances.

        Returns:
            Dictionary of plugin instances
        """
        return self._plugin_instances.copy()
