"""Plugin manager for discovering and loading Santiq plugins"""


import importlib
import importlib.metadata
import os
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional, Union, Type
from .. import __version__ as core_full_version

import yaml
from packaging import version

from santiq.core.exceptions import PluginError, PluginLoadError, PluginNotFoundError, PluginVersionError
from santiq.plugins.base.extractor import ExtractorPlugin
from santiq.plugins.base.profiler import ProfilerPlugin
from santiq.plugins.base.transformer import TransformerPlugin
from santiq.plugins.base.loader import LoaderPlugin


PluginType = Union[ExtractorPlugin, ProfilerPlugin, TransformerPlugin, LoaderPlugin]
PluginClass = Type[PluginType]

class PluginManager:
    """Manages plugin discovery , loading and lifecycle"""
    
    Plugin_Types = {
        "extractor": ExtractorPlugin,
        "profiler": ProfilerPlugin,
        "transformer": TransformerPlugin,
        "loader": LoaderPlugin
    }
    
    def __init__(self, local_plugin_dirs: Optional[List[str]] = None) -> None:
        self.local_plugin_dirs = local_plugin_dirs or []
        self._loaded_plugins: Dict[str, Dict[str, PluginClass]] = {
            plugin_type: {} for plugin_type in self.Plugin_Types
        }
        self._plugin_instances: Dict[str, PluginType] = {}
        
    def discover_plugins(self) -> Dict[str, List[Dict[str, Any]]]:
        """Discover all available plugins"""
        plugins = {plugin_type: [] for plugin_type in self.Plugin_Types}
        
        # Discover entry point plugins
        for plugin_type in self.PLUGIN_TYPES:
            entry_point_group = f"Santiq.{plugin_type}s"
            for entry_point in importlib.metadata.entry_points().select(group=entry_point_group):
                try:
                    plugin_info = self._get_plugin_info_from_entry_point(entry_point, plugin_type)
                    plugins[plugin_type].append(plugin_info)
                except Exception as e:
                    print(f"Warning: Failed to load plugin {entry_point.name}: {e}")
        
        # Discover local plugins
        for plugin_dir in self.local_plugin_dirs:
            local_plugins = self._discover_local_plugins(plugin_dir)
            for plugin_type, plugin_list in local_plugins.items():
                plugins[plugin_type].extend(plugin_list)
        
        return plugins
    
    def _get_plugin_info_from_entry_point(
        self, entry_point: importlib.metadata.EntryPoint, plugin_type: str) -> Dict[str, Any]:
        """Get plugin information from an entry point."""
        try:
            plugin_class = entry_point.load()
            return {
                "name": entry_point.name,
                "class": plugin_class,
                "plugin_name": getattr(plugin_class, "__plugin_name__", entry_point.name),
                "version": getattr(plugin_class, "__version__", "unknown"),
                "api_version": getattr(plugin_class, "__api_version__", "1.0"),
                "description": getattr(plugin_class, "__description__", ""),
                "source": "entry_point",
                "entry_point": entry_point,
            }
        except Exception as e:
            raise PluginLoadError(entry_point.name, e)
        
        
    def _discover_local_plugins(self, plugin_dir: str) -> Dict[str, List[Dict[str, Any]]]:
        """Discover plugins in local directories."""
        plugins = {plugin_type: [] for plugin_type in self.PLUGIN_TYPES}
        plugin_path = Path(plugin_dir)
        
        if not plugin_path.exists():
            return plugins
        
        for manifest_file in plugin_path.rglob("plugin.yml"):
            try:
                with open(manifest_file) as f:
                    manifest = yaml.safe_load(f)
                
                plugin_info = self._load_local_plugin(manifest_file.parent, manifest)
                plugin_type = manifest.get("type")
                if plugin_type in plugins:
                    plugins[plugin_type].append(plugin_info)
            except Exception as e:
                print(f"Warning: Failed to load local plugin {manifest_file}: {e}")
        
        return plugins
    
    
    def _load_local_plugin(self, plugin_dir: Path, manifest: Dict[str, Any]) -> Dict[str, Any]:
        """Load a local plugin from manifest."""
        # Add plugin directory to Python path temporarily
        if str(plugin_dir) not in sys.path:
            sys.path.insert(0, str(plugin_dir))
        
        try:
            entry_point_str = manifest["entry_point"]
            module_name, class_name = entry_point_str.split(":")
            module = importlib.import_module(module_name)
            plugin_class = getattr(module, class_name)
            
            return {
                "name": manifest["name"],
                "class": plugin_class,
                "plugin_name": manifest.get("plugin_name", manifest["name"]),
                "version": manifest.get("version", "unknown"),
                "api_version": manifest.get("api_version", "1.0"),
                "description": manifest.get("description", ""),
                "source": "local",
                "manifest": manifest,
                "path": str(plugin_dir),
            }
        finally:
            # Remove from path
            if str(plugin_dir) in sys.path:
                sys.path.remove(str(plugin_dir))
                
    
    def load_plugin(self, plugin_name: str, plugin_type: str) -> PluginClass:
        """Load a specific plugin by name and type."""
        if plugin_type not in self.PLUGIN_TYPES:
            raise PluginError(f"Unknown plugin type: {plugin_type}")
        
        # Check if already loaded
        if plugin_name in self._loaded_plugins[plugin_type]:
            return self._loaded_plugins[plugin_type][plugin_name]
        
        # Discover and load
        plugins = self.discover_plugins()
        for plugin_info in plugins[plugin_type]:
            if plugin_info["name"] == plugin_name:
                plugin_class = plugin_info["class"]
                
                # Validate API version
                self._validate_api_version(plugin_info)
                
                # Validate inheritance
                expected_base = self.PLUGIN_TYPES[plugin_type]
                if not issubclass(plugin_class, expected_base):
                    raise PluginLoadError(
                        plugin_name,
                        Exception(f"Plugin must inherit from {expected_base.__name__}")
                    )
                
                self._loaded_plugins[plugin_type][plugin_name] = plugin_class
                return plugin_class
        
        raise PluginNotFoundError(plugin_name, plugin_type)
    
    
    def _validate_api_version(self, plugin_info: Dict[str, Any]) -> None:
        """Validate plugin API version compatibility."""
        plugin_api_version = plugin_info.get("api_version", "1.0")
        core_version_parsed = version.parse(core_full_version)
        
        try:
            if not version.parse(plugin_api_version).major == core_version_parsed.major:
                raise PluginVersionError(
                    plugin_info["name"],
                    f"~={core_version_parsed}",
                    plugin_api_version
                )
        except version.InvalidVersion:
            raise PluginVersionError(
                plugin_info["name"],
                "valid semantic version",
                plugin_api_version
            )
            
    def create_plugin_instance(self, plugin_name: str, plugin_type: str, config: Dict[str, Any]) -> PluginType:
        """Create and configure a plugin instance."""
        plugin_class = self.load_plugin(plugin_name, plugin_type)
        instance = plugin_class()
        instance.setup(config)
        
        instance_key = f"{plugin_type}:{plugin_name}"
        self._plugin_instances[instance_key] = instance
        
        return instance
    
    def cleanup_plugin_instance(self, plugin_name: str, plugin_type: str) -> None:
        """Cleanup a plugin instance."""
        instance_key = f"{plugin_type}:{plugin_name}"
        if instance_key in self._plugin_instances:
            self._plugin_instances[instance_key].teardown()
            del self._plugin_instances[instance_key]
    
    def list_plugins(self, plugin_type: Optional[str] = None) -> Dict[str, List[Dict[str, Any]]]:
        """List all available plugins."""
        discovered = self.discover_plugins()
        
        if plugin_type:
            if plugin_type not in self.PLUGIN_TYPES:
                raise PluginError(f"Unknown plugin type: {plugin_type}")
            return {plugin_type: discovered[plugin_type]}
        
        return discovered