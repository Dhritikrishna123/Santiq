"""Plugin validation functionality."""

import importlib
import importlib.util
import sys
from pathlib import Path
from typing import Any, Dict, Type

from santiq.core.exceptions import PluginLoadError
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


class PluginValidator:
    """Validates plugin compatibility and requirements.

    This class provides methods to validate that plugins:
    - Inherit from the correct base class
    - Have required methods
    - Meet API version requirements
    """

    @staticmethod
    def validate_plugin_class(
        plugin_class: PluginClass, plugin_type: str, plugin_name: str
    ) -> None:
        """Validate that a plugin class meets requirements.

        Args:
            plugin_class: The plugin class to validate
            plugin_type: Type of plugin (extractor, profiler, transformer, loader)
            plugin_name: Name of the plugin for error messages

        Raises:
            PluginLoadError: If the plugin fails validation
        """
        if plugin_type not in PLUGIN_TYPES:
            raise PluginLoadError(
                plugin_name,
                Exception(f"Unknown plugin type: {plugin_type}"),
            )

        expected_base = PLUGIN_TYPES[plugin_type]
        if not issubclass(plugin_class, expected_base):
            raise PluginLoadError(
                plugin_name,
                Exception(f"Plugin must inherit from {expected_base.__name__}"),
            )

        # Validate required methods based on plugin type
        PluginValidator._validate_required_methods(plugin_class, plugin_type, plugin_name)

    @staticmethod
    def _validate_required_methods(
        plugin_class: PluginClass, plugin_type: str, plugin_name: str
    ) -> None:
        """Validate that a plugin has required methods.

        Args:
            plugin_class: The plugin class to validate
            plugin_type: Type of plugin
            plugin_name: Name of the plugin for error messages

        Raises:
            PluginLoadError: If required methods are missing
        """
        required_methods = {
            "extractor": ["extract"],
            "transformer": ["transform"],
            "profiler": ["profile"],
            "loader": ["load"],
        }

        if plugin_type not in required_methods:
            return

        for method_name in required_methods[plugin_type]:
            if not hasattr(plugin_class, method_name) or not callable(
                getattr(plugin_class, method_name)
            ):
                raise PluginLoadError(
                    plugin_name,
                    Exception(
                        f"{plugin_type.capitalize()} plugin must implement {method_name}() method"
                    ),
                )

    @staticmethod
    def validate_manifest(manifest: Dict[str, Any], plugin_name: str) -> None:
        """Validate plugin manifest structure.

        Args:
            manifest: Plugin manifest data
            plugin_name: Name of the plugin for error messages

        Raises:
            PluginLoadError: If manifest is invalid
        """
        required_fields = ["name", "entry_point", "type"]
        for field in required_fields:
            if field not in manifest:
                raise PluginLoadError(
                    plugin_name,
                    Exception(f"Missing required field '{field}' in manifest"),
                )

        # Validate entry point format
        entry_point_str = manifest["entry_point"]
        if ":" not in entry_point_str:
            raise PluginLoadError(
                plugin_name,
                Exception("entry_point must be in format 'module:class'"),
            )

        # Validate plugin type
        plugin_type = manifest["type"]
        if plugin_type not in PLUGIN_TYPES:
            raise PluginLoadError(
                plugin_name,
                Exception(f"Unknown plugin type: {plugin_type}"),
            )

    @staticmethod
    def load_plugin_from_entry_point(
        entry_point_str: str, plugin_dir: Path, plugin_name: str
    ) -> PluginClass:
        """Load a plugin class from an entry point string.

        Args:
            entry_point_str: Entry point string in format 'module:class'
            plugin_dir: Directory containing the plugin
            plugin_name: Name of the plugin for error messages

        Returns:
            The loaded plugin class

        Raises:
            PluginLoadError: If the plugin fails to load
        """
        module_name, class_name = entry_point_str.split(":", 1)

        # Add plugin directory to Python path temporarily
        plugin_dir_str = str(plugin_dir)
        path_added = False

        try:
            if plugin_dir_str not in sys.path:
                sys.path.insert(0, plugin_dir_str)
                path_added = True

            # Try to import the module
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

            # Get the class from the module
            if not hasattr(module, class_name):
                raise PluginLoadError(
                    plugin_name,
                    Exception(
                        f"Class '{class_name}' not found in module '{module_name}'"
                    ),
                )

            return getattr(module, class_name)

        finally:
            # Remove from path if we added it
            if path_added and plugin_dir_str in sys.path:
                sys.path.remove(plugin_dir_str)
