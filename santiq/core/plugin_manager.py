"""Plugin manager for discovering and loading Santiq plugins"""

import importlib
import importlib.metadata
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Type, Union

import yaml
from packaging import version

from santiq import __version__ as core_full_version
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

PluginType = Union[ExtractorPlugin, ProfilerPlugin, TransformerPlugin, LoaderPlugin]
PluginClass = Type[PluginType]


class PluginManager:
    """Manages plugin discovery, loading and lifecycle"""

    PLUGIN_TYPES = {  # Fixed: was Plugin_Types (inconsistent casing)
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
        self.local_plugin_dirs = local_plugin_dirs or []
        self.external_plugin_config = external_plugin_config
        self._loaded_plugins: Dict[str, Dict[str, PluginClass]] = {
            plugin_type: {} for plugin_type in self.PLUGIN_TYPES
        }
        self._plugin_instances: Dict[str, PluginType] = {}
        self._external_plugins: Dict[str, Dict[str, Any]] = {}
        self._load_external_plugin_config()

    def _load_external_plugin_config(self) -> None:
        """Load external plugin configuration from file."""
        if not self.external_plugin_config:
            # Try to find default config file
            default_configs = [
                os.path.expanduser("~/.santiq/external_plugins.yml"),
                os.path.expanduser("~/.santiq/external_plugins.yaml"),
                ".santiq/external_plugins.yml",
                ".santiq/external_plugins.yaml",
            ]

            for config_path in default_configs:
                if os.path.exists(config_path):
                    self.external_plugin_config = config_path
                    break

        if self.external_plugin_config and os.path.exists(self.external_plugin_config):
            try:
                with open(self.external_plugin_config, "r", encoding="utf-8") as f:
                    config = yaml.safe_load(f)
                    if isinstance(config, dict):
                        self._external_plugins = config.get("plugins", {})
            except Exception as e:
                print(
                    f"Warning: Failed to load external plugin config {self.external_plugin_config}: {e}"
                )

    def discover_plugins(self) -> Dict[str, List[Dict[str, Any]]]:
        """Discover all available plugins from entry points, local directories, and external config.

        Returns:
            Dictionary mapping plugin types to lists of plugin information
        """
        plugins: Dict[str, List[Dict[str, Any]]] = {
            plugin_type: [] for plugin_type in self.PLUGIN_TYPES
        }

        # Discover entry point plugins (built-in and installed from PyPI)
        for plugin_type in self.PLUGIN_TYPES:  # Fixed: was self.Plugin_Types
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

        # Discover external plugins from configuration
        external_plugins = self._discover_external_plugins()
        for plugin_type, plugin_list in external_plugins.items():
            plugins[plugin_type].extend(plugin_list)

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
            expected_base = self.PLUGIN_TYPES[plugin_type]
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
            plugin_type: [] for plugin_type in self.PLUGIN_TYPES
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

                if plugin_type not in self.PLUGIN_TYPES:
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
            if plugin_type in self.PLUGIN_TYPES:
                expected_base = self.PLUGIN_TYPES[plugin_type]
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

    def _discover_external_plugins(self) -> Dict[str, List[Dict[str, Any]]]:
        """Discover external plugins from configuration.

        Returns:
            Dictionary mapping plugin types to lists of plugin information
        """
        plugins: Dict[str, List[Dict[str, Any]]] = {
            plugin_type: [] for plugin_type in self.PLUGIN_TYPES
        }

        for plugin_name, plugin_config in self._external_plugins.items():
            try:
                plugin_type = plugin_config.get("type")
                if plugin_type not in self.PLUGIN_TYPES:
                    print(
                        f"Warning: Unknown plugin type '{plugin_type}' for {plugin_name}"
                    )
                    continue

                # Check if plugin is installed
                package_name = plugin_config.get("package")
                if package_name and self._is_package_installed(package_name):
                    plugin_info = {
                        "name": plugin_name,
                        "package": package_name,
                        "type": plugin_type,
                        "version": plugin_config.get("version", "unknown"),
                        "api_version": plugin_config.get("api_version", "1.0"),
                        "description": plugin_config.get("description", ""),
                        "source": "external",
                        "config": plugin_config,
                        "installed": True,
                    }
                    plugins[plugin_type].append(plugin_info)
                else:
                    # Plugin configured but not installed
                    plugin_info = {
                        "name": plugin_name,
                        "package": package_name,
                        "type": plugin_type,
                        "version": plugin_config.get("version", "unknown"),
                        "api_version": plugin_config.get("api_version", "1.0"),
                        "description": plugin_config.get("description", ""),
                        "source": "external",
                        "config": plugin_config,
                        "installed": False,
                    }
                    plugins[plugin_type].append(plugin_info)

            except Exception as e:
                print(f"Warning: Failed to process external plugin {plugin_name}: {e}")

        return plugins

    def _is_package_installed(self, package_name: str) -> bool:
        """Check if a package is installed.

        Args:
            package_name: Name of the package to check

        Returns:
            True if package is installed, False otherwise
        """
        try:
            importlib.metadata.distribution(package_name)
            return True
        except importlib.metadata.PackageNotFoundError:
            return False

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
        if not package_name:
            package_name = plugin_name

        try:
            cmd = [sys.executable, "-m", "pip", "install"]

            if upgrade:
                cmd.append("--upgrade")

            if source:
                cmd.extend(["--index-url", source])

            cmd.append(package_name)

            result = subprocess.run(cmd, capture_output=True, text=True, check=True)

            # Reload external plugin configuration
            self._load_external_plugin_config()

            return True

        except subprocess.CalledProcessError as e:
            print(f"Failed to install {package_name}: {e.stderr}")
            return False
        except Exception as e:
            print(f"Error installing {package_name}: {e}")
            return False

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
        if not package_name:
            package_name = plugin_name

        try:
            cmd = [sys.executable, "-m", "pip", "uninstall", "-y", package_name]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)

            # Reload external plugin configuration
            self._load_external_plugin_config()

            return True

        except subprocess.CalledProcessError as e:
            print(f"Failed to uninstall {package_name}: {e.stderr}")
            return False
        except Exception as e:
            print(f"Error uninstalling {package_name}: {e}")
            return False

    def add_external_plugin_config(
        self, plugin_name: str, plugin_config: Dict[str, Any]
    ) -> None:
        """Add external plugin configuration.

        Args:
            plugin_name: Name of the plugin
            plugin_config: Plugin configuration dictionary
        """
        self._external_plugins[plugin_name] = plugin_config
        self._save_external_plugin_config()

    def remove_external_plugin_config(self, plugin_name: str) -> None:
        """Remove external plugin configuration.

        Args:
            plugin_name: Name of the plugin to remove
        """
        if plugin_name in self._external_plugins:
            del self._external_plugins[plugin_name]
            self._save_external_plugin_config()

    def _save_external_plugin_config(self) -> None:
        """Save external plugin configuration to file."""
        if not self.external_plugin_config:
            # Create default config directory
            config_dir = os.path.expanduser("~/.santiq")
            os.makedirs(config_dir, exist_ok=True)
            self.external_plugin_config = os.path.join(
                config_dir, "external_plugins.yml"
            )

        try:
            config_data = {"plugins": self._external_plugins}
            with open(self.external_plugin_config, "w", encoding="utf-8") as f:
                yaml.dump(
                    config_data, f, default_flow_style=False, sort_keys=True, indent=2
                )
        except Exception as e:
            print(f"Warning: Failed to save external plugin config: {e}")

    def get_external_plugin_info(self, plugin_name: str) -> Optional[Dict[str, Any]]:
        """Get information about an external plugin.

        Args:
            plugin_name: Name of the plugin

        Returns:
            Plugin configuration if found, None otherwise
        """
        return self._external_plugins.get(plugin_name)

    def list_external_plugins(self) -> Dict[str, List[Dict[str, Any]]]:
        """List all configured external plugins.

        Returns:
            Dictionary mapping plugin types to lists of external plugin information
        """
        return self._discover_external_plugins()

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
        if plugin_type not in self.PLUGIN_TYPES:
            raise PluginError(f"Unknown plugin type: {plugin_type}")

        # Check if already loaded
        if plugin_name in self._loaded_plugins[plugin_type]:
            return self._loaded_plugins[plugin_type][plugin_name]

        # Discover and load
        plugins = self.discover_plugins()
        for plugin_info in plugins[plugin_type]:
            if plugin_info["name"] == plugin_name:
                # Validate API version
                self._validate_api_version(plugin_info)

                plugin_class = plugin_info["class"]
                # Type cast to ensure proper typing
                typed_plugin_class: PluginClass = plugin_class
                self._loaded_plugins[plugin_type][plugin_name] = typed_plugin_class
                return typed_plugin_class

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
        plugin_class = self.load_plugin(plugin_name, plugin_type)

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
