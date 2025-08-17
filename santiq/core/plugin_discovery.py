"""Plugin discovery functionality for Santiq."""

import importlib
import importlib.metadata
import importlib.util
import sys
from pathlib import Path
from typing import Any, Dict, List

import yaml

from santiq.core.exceptions import PluginLoadError
from santiq.plugins.base.extractor import ExtractorPlugin
from santiq.plugins.base.loader import LoaderPlugin
from santiq.plugins.base.profiler import ProfilerPlugin
from santiq.plugins.base.transformer import TransformerPlugin

PluginType = ExtractorPlugin | ProfilerPlugin | TransformerPlugin | LoaderPlugin
PluginClass = type[PluginType]

PLUGIN_TYPES = {
    "extractor": ExtractorPlugin,
    "profiler": ProfilerPlugin,
    "transformer": TransformerPlugin,
    "loader": LoaderPlugin,
}


class PluginDiscovery:
    """Handles discovery of plugins from various sources."""

    def __init__(self, local_plugin_dirs: List[str] | None = None) -> None:
        """Initialize plugin discovery.

        Args:
            local_plugin_dirs: List of local directories to search for plugins
        """
        self.local_plugin_dirs = local_plugin_dirs or []

    def discover_all_plugins(self) -> Dict[str, List[Dict[str, Any]]]:
        """Discover all available plugins from entry points and local directories.

        Returns:
            Dictionary mapping plugin types to lists of plugin information
        """
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

        # Discover local plugins
        for plugin_dir in self.local_plugin_dirs:
            try:
                local_plugins = self._discover_local_plugins(plugin_dir)
                for plugin_type, plugin_list in local_plugins.items():
                    plugins[plugin_type].extend(plugin_list)
            except PluginLoadError:
                # Re-raise PluginLoadError to maintain validation behavior
                raise
            except Exception as e:
                print(f"Warning: Failed to discover local plugins in {plugin_dir}: {e}")

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
            expected_base = PLUGIN_TYPES[plugin_type]
            if not issubclass(plugin_class, expected_base):
                raise PluginLoadError(
                    entry_point.name,
                    Exception(f"Plugin must inherit from {expected_base.__name__}"),
                )

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

    def _discover_local_plugins(
        self, plugin_dir: str
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Discover plugins in local directories.

        Args:
            plugin_dir: Directory path to search for plugins

        Returns:
            Dictionary mapping plugin types to lists of plugin information
        """
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
        required_fields = ["name", "entry_point", "type"]
        for field in required_fields:
            if field not in manifest:
                raise PluginLoadError(
                    manifest.get("name", "unknown"),
                    Exception(f"Missing required field '{field}' in manifest"),
                )

        plugin_name = manifest["name"]

        # Add plugin directory to Python path temporarily
        plugin_dir_str = str(plugin_dir)
        path_added = False

        try:
            if plugin_dir_str not in sys.path:
                sys.path.insert(0, plugin_dir_str)
                path_added = True

            entry_point_str = manifest["entry_point"]

            if ":" not in entry_point_str:
                raise PluginLoadError(
                    plugin_name,
                    Exception("entry_point must be in format 'module:class'"),
                )

            module_name, class_name = entry_point_str.split(":", 1)

            try:
                # Check if module already exists and force reload
                if module_name in sys.modules:
                    del sys.modules[module_name]
                module = importlib.import_module(module_name)
            except ImportError as e:
                # Try to load the module from the plugin directory
                try:
                    module_file = plugin_dir / f"{module_name}.py"
                    spec = importlib.util.spec_from_file_location(
                        module_name, module_file
                    )
                    if spec and spec.loader:
                        module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(module)
                        # Ensure the module is registered in sys.modules
                        sys.modules[module_name] = module
                    else:
                        raise PluginLoadError(plugin_name, e)
                except Exception as load_error:
                    raise PluginLoadError(plugin_name, e) from load_error

            if not hasattr(module, class_name):
                raise PluginLoadError(
                    plugin_name,
                    Exception(
                        f"Class '{class_name}' not found in module '{module_name}'"
                    ),
                )

            plugin_class = getattr(module, class_name)

            # Validate that the plugin inherits from the correct base class
            plugin_type = manifest["type"]
            if plugin_type in PLUGIN_TYPES:
                expected_base = PLUGIN_TYPES[plugin_type]
                if not issubclass(plugin_class, expected_base):
                    raise PluginLoadError(
                        plugin_name,
                        Exception(f"Plugin must inherit from {expected_base.__name__}"),
                    )

            # Validate that the plugin has required methods
            if plugin_type == "extractor":
                if not hasattr(plugin_class, "extract") or not callable(
                    getattr(plugin_class, "extract")
                ):
                    raise PluginLoadError(
                        plugin_name,
                        Exception("Extractor plugin must implement extract() method"),
                    )
            elif plugin_type == "transformer":
                if not hasattr(plugin_class, "transform") or not callable(
                    getattr(plugin_class, "transform")
                ):
                    raise PluginLoadError(
                        plugin_name,
                        Exception(
                            "Transformer plugin must implement transform() method"
                        ),
                    )
            elif plugin_type == "profiler":
                if not hasattr(plugin_class, "profile") or not callable(
                    getattr(plugin_class, "profile")
                ):
                    raise PluginLoadError(
                        plugin_name,
                        Exception("Profiler plugin must implement profile() method"),
                    )
            elif plugin_type == "loader":
                if not hasattr(plugin_class, "load") or not callable(
                    getattr(plugin_class, "load")
                ):
                    raise PluginLoadError(
                        plugin_name,
                        Exception("Loader plugin must implement load() method"),
                    )

            return {
                "name": plugin_name,
                "class": plugin_class,
                "plugin_name": manifest.get("plugin_name", plugin_name),
                "version": manifest.get("version", "unknown"),
                "api_version": manifest.get("api_version", "1.0"),
                "description": manifest.get("description", ""),
                "source": "local",
                "manifest": manifest,
                "path": plugin_dir_str,
                "plugin_type": plugin_type,
            }

        finally:
            # Remove from path if we added it
            if path_added and plugin_dir_str in sys.path:
                sys.path.remove(plugin_dir_str)
