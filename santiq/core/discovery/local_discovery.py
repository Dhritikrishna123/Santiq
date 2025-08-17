"""Local plugin discovery functionality."""

from pathlib import Path
from typing import Any, Dict, List

import yaml

from santiq.core.discovery.plugin_validator import PluginValidator
from santiq.core.exceptions import PluginLoadError


class LocalDiscovery:
    """Handles discovery of plugins from local directories.

    This class discovers plugins that are stored in local directories
    with plugin.yml manifest files.
    """

    def __init__(self) -> None:
        """Initialize local discovery."""
        pass

    def discover_local_plugins(
        self, plugin_dirs: List[str]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Discover plugins in local directories.

        Args:
            plugin_dirs: List of directory paths to search for plugins

        Returns:
            Dictionary mapping plugin types to lists of plugin information
        """
        from santiq.core.discovery.plugin_validator import PLUGIN_TYPES

        plugins: Dict[str, List[Dict[str, Any]]] = {
            plugin_type: [] for plugin_type in PLUGIN_TYPES
        }

        for plugin_dir in plugin_dirs:
            try:
                local_plugins = self._discover_plugins_in_directory(plugin_dir)
                for plugin_type, plugin_list in local_plugins.items():
                    plugins[plugin_type].extend(plugin_list)
            except PluginLoadError:
                # Re-raise PluginLoadError to maintain validation behavior
                raise
            except Exception as e:
                print(f"Warning: Failed to discover local plugins in {plugin_dir}: {e}")

        return plugins

    def _discover_plugins_in_directory(
        self, plugin_dir: str
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Discover plugins in a specific directory.

        Args:
            plugin_dir: Directory path to search for plugins

        Returns:
            Dictionary mapping plugin types to lists of plugin information
        """
        from santiq.core.discovery.plugin_validator import PLUGIN_TYPES

        plugins: Dict[str, List[Dict[str, Any]]] = {
            plugin_type: [] for plugin_type in PLUGIN_TYPES
        }
        plugin_path = Path(plugin_dir)

        if not plugin_path.exists():
            print(f"Warning: Plugin directory {plugin_dir} does not exist")
            return plugins

        if not plugin_path.is_dir():
            print(f"Warning: {plugin_dir} is not a directory")
            return plugins

        for manifest_file in plugin_path.rglob("plugin.yml"):
            try:
                with open(manifest_file, "r", encoding="utf-8") as f:
                    manifest = yaml.safe_load(f)

                if not isinstance(manifest, dict):
                    print(f"Warning: Invalid manifest format in {manifest_file}")
                    continue

                plugin_info = self._load_local_plugin(manifest_file.parent, manifest)
                plugin_type = manifest.get("type")

                if plugin_type not in PLUGIN_TYPES:
                    print(
                        f"Warning: Unknown plugin type '{plugin_type}' in {manifest_file}"
                    )
                    continue

                plugins[plugin_type].append(plugin_info)

            except yaml.YAMLError as e:
                print(f"Warning: Failed to parse YAML in {manifest_file}: {e}")
            except PluginLoadError:
                # Re-raise PluginLoadError to maintain validation behavior
                raise
            except Exception as e:
                print(f"Warning: Failed to load local plugin {manifest_file}: {e}")

        return plugins

    def _load_local_plugin(
        self, plugin_dir: Path, manifest: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Load a local plugin from manifest.

        Args:
            plugin_dir: Directory containing the plugin
            manifest: Plugin manifest data

        Returns:
            Dictionary containing plugin information

        Raises:
            PluginLoadError: If the plugin fails to load
        """
        plugin_name = manifest.get("name", "unknown")
        
        # Validate manifest structure
        PluginValidator.validate_manifest(manifest, plugin_name)

        # Load plugin class
        plugin_class = PluginValidator.load_plugin_from_entry_point(
            manifest["entry_point"], plugin_dir, plugin_name
        )

        # Validate plugin class
        plugin_type = manifest["type"]
        PluginValidator.validate_plugin_class(plugin_class, plugin_type, plugin_name)

        return {
            "name": plugin_name,
            "class": plugin_class,
            "plugin_name": manifest.get("plugin_name", plugin_name),
            "version": manifest.get("version", "unknown"),
            "api_version": manifest.get("api_version", "1.0"),
            "description": manifest.get("description", ""),
            "source": "local",
            "manifest": manifest,
            "path": str(plugin_dir),
            "plugin_type": plugin_type,
        }
