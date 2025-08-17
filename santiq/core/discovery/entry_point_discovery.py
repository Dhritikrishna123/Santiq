"""Entry point plugin discovery functionality."""

import importlib.metadata
from typing import Any, Dict, List

from santiq.core.discovery.plugin_validator import PluginValidator
from santiq.core.exceptions import PluginLoadError


class EntryPointDiscovery:
    """Handles discovery of plugins from entry points.

    This class discovers plugins that are installed via PyPI or built-in
    to the system using Python's entry point mechanism.
    """

    def __init__(self) -> None:
        """Initialize entry point discovery."""
        pass

    def discover_entry_point_plugins(self) -> Dict[str, List[Dict[str, Any]]]:
        """Discover all plugins from entry points.

        Returns:
            Dictionary mapping plugin types to lists of plugin information
        """
        from santiq.core.discovery.plugin_validator import PLUGIN_TYPES

        plugins: Dict[str, List[Dict[str, Any]]] = {
            plugin_type: [] for plugin_type in PLUGIN_TYPES
        }

        # Discover entry point plugins (built-in and installed from PyPI)
        for plugin_type in PLUGIN_TYPES:
            entry_point_group = f"santiq.{plugin_type}s"
            try:
                entry_points = importlib.metadata.entry_points().select(
                    group=entry_point_group
                )
                for entry_point in entry_points:
                    try:
                        plugin_info = self._get_plugin_info_from_entry_point(
                            entry_point, plugin_type
                        )
                        plugins[plugin_type].append(plugin_info)
                    except Exception as e:
                        print(f"Warning: Failed to load plugin {entry_point.name}: {e}")
            except Exception as e:
                print(
                    f"Warning: Failed to discover entry points for {plugin_type}: {e}"
                )

        return plugins

    def _get_plugin_info_from_entry_point(
        self, entry_point: importlib.metadata.EntryPoint, plugin_type: str
    ) -> Dict[str, Any]:
        """Get plugin information from an entry point.

        Args:
            entry_point: The entry point to load
            plugin_type: Type of plugin (extractor, profiler, etc.)

        Returns:
            Dictionary containing plugin information

        Raises:
            PluginLoadError: If the plugin fails to load
        """
        try:
            plugin_class = entry_point.load()

            # Validate that the plugin inherits from the correct base class
            PluginValidator.validate_plugin_class(plugin_class, plugin_type, entry_point.name)

            return {
                "name": entry_point.name,
                "class": plugin_class,
                "plugin_name": getattr(
                    plugin_class, "__plugin_name__", entry_point.name
                ),
                "version": getattr(plugin_class, "__version__", "unknown"),
                "api_version": getattr(plugin_class, "__api_version__", "1.0"),
                "description": getattr(plugin_class, "__description__", ""),
                "source": "entry_point",
                "entry_point": entry_point,
                "plugin_type": plugin_type,
            }
        except Exception as e:
            raise PluginLoadError(entry_point.name, e)
