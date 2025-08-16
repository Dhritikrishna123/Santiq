"""Main ETL engine that orchestrates the entire pipeline."""

import uuid
from typing import Any, Dict, List, Optional

from santiq.core.audit import AuditLogger
from santiq.core.config import ConfigManager, PipelineConfig
from santiq.core.pipeline import Pipeline
from santiq.core.plugin_manager import PluginManager


class ETLEngine:
    """Main engine for executing ETL pipelines."""
    
    def __init__(
        self,
        local_plugin_dirs: Optional[List[str]] = None,
        external_plugin_config: Optional[str] = None,
        audit_log_file: Optional[str] = None
    ) -> None:
        self.plugin_manager = PluginManager(local_plugin_dirs, external_plugin_config)
        self.audit_logger = AuditLogger(audit_log_file)
        self.config_manager = ConfigManager()
        self.pipeline = Pipeline(self.plugin_manager, self.audit_logger, self.config_manager)
    
    def run_pipeline(
        self,
        config_path: str,
        mode: str = "manual",
        pipeline_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Run a pipeline from configuration file."""
        config = self.config_manager.load_pipeline_config(config_path)
        return self.pipeline.execute(config, mode, pipeline_id)
    
    def run_pipeline_from_config(
        self,
        config: PipelineConfig,
        mode: str = "manual",
        pipeline_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Run a pipeline from configuration object."""
        return self.pipeline.execute(config, mode, pipeline_id)
    
    def run_pipeline_from_file(
        self,
        config_path: str,
        mode: str = "manual",
        pipeline_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Run a pipeline from configuration file."""
        config = self.config_manager.load_pipeline_config(config_path)
        return self.pipeline.execute(config, mode, pipeline_id)
    
    def list_plugins(self, plugin_type: Optional[str] = None) -> Dict[str, List[Dict[str, Any]]]:
        """List all available plugins."""
        return self.plugin_manager.list_plugins(plugin_type)
    
    def list_external_plugins(self) -> Dict[str, List[Dict[str, Any]]]:
        """List all configured external plugins."""
        return self.plugin_manager.list_external_plugins()
    
    def add_external_plugin_config(self, plugin_name: str, plugin_config: Dict[str, Any]) -> None:
        """Add external plugin configuration."""
        self.plugin_manager.add_external_plugin_config(plugin_name, plugin_config)
    
    def remove_external_plugin_config(self, plugin_name: str) -> None:
        """Remove external plugin configuration."""
        self.plugin_manager.remove_external_plugin_config(plugin_name)
    
    def get_external_plugin_info(self, plugin_name: str) -> Optional[Dict[str, Any]]:
        """Get information about an external plugin."""
        return self.plugin_manager.get_external_plugin_info(plugin_name)
    
    def install_external_plugin(self, plugin_name: str, package_name: Optional[str] = None,
                               source: Optional[str] = None, upgrade: bool = False) -> bool:
        """Install an external plugin package."""
        return self.plugin_manager.install_external_plugin(plugin_name, package_name, source, upgrade)
    
    def uninstall_external_plugin(self, plugin_name: str, package_name: Optional[str] = None) -> bool:
        """Uninstall an external plugin package."""
        return self.plugin_manager.uninstall_external_plugin(plugin_name, package_name)
    
    def is_package_installed(self, package_name: str) -> bool:
        """Check if a package is installed.
        
        Args:
            package_name: Name of the package to check
            
        Returns:
            True if package is installed, False otherwise
        """
        return self.plugin_manager._is_package_installed(package_name)
    
    def get_pipeline_history(self, pipeline_id: str) -> List[Dict[str, Any]]:
        """Get execution history for a pipeline."""
        events = self.audit_logger.get_pipeline_events(pipeline_id)
        return [event.model_dump() for event in events]
    
    def get_recent_executions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent pipeline executions."""
        events = self.audit_logger.get_recent_events(limit)
        pipeline_events = [e for e in events if e.event_type == "pipeline_start"]
        return [event.model_dump() for event in pipeline_events]
    
    def get_audit_log(self, pipeline_id: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get audit log entries.
        
        Args:
            pipeline_id: Optional pipeline ID to filter events
            limit: Maximum number of events to return
            
        Returns:
            List of audit events as dictionaries
        """
        if pipeline_id:
            events = self.audit_logger.get_pipeline_events(pipeline_id)
        else:
            events = self.audit_logger.get_recent_events(limit)
        
        return [event.model_dump() for event in events]
