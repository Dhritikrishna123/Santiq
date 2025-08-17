"""External plugin management functionality for Santiq."""

import importlib.metadata
import os
import subprocess
import sys
from typing import Any, Dict, List, Optional

import yaml

from santiq.plugins.base.extractor import ExtractorPlugin
from santiq.plugins.base.loader import LoaderPlugin
from santiq.plugins.base.profiler import ProfilerPlugin
from santiq.plugins.base.transformer import TransformerPlugin

PluginType = ExtractorPlugin | ProfilerPlugin | TransformerPlugin | LoaderPlugin

PLUGIN_TYPES = {
    "extractor": ExtractorPlugin,
    "profiler": ProfilerPlugin,
    "transformer": TransformerPlugin,
    "loader": LoaderPlugin,
}


class ExternalPluginManager:
    """Manages external plugin configuration and installation."""

    def __init__(self, external_plugin_config: Optional[str] = None) -> None:
        """Initialize external plugin manager.

        Args:
            external_plugin_config: Path to external plugin configuration file
        """
        self.external_plugin_config = external_plugin_config
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

    def discover_external_plugins(self) -> Dict[str, List[Dict[str, Any]]]:
        """Discover external plugins from configuration.

        Returns:
            Dictionary mapping plugin types to lists of plugin information
        """
        plugins: Dict[str, List[Dict[str, Any]]] = {
            plugin_type: [] for plugin_type in PLUGIN_TYPES
        }

        for plugin_name, plugin_config in self._external_plugins.items():
            try:
                plugin_type = plugin_config.get("type")
                if plugin_type not in PLUGIN_TYPES:
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
        return self.discover_external_plugins()
