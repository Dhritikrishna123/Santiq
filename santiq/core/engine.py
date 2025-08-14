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
        audit_log_file: Optional[str] = None
    ) -> None:
        self.plugin_manager = PluginManager(local_plugin_dirs)
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
    
    def list_plugins(self, plugin_type: Optional[str] = None) -> Dict[str, List[Dict[str, Any]]]:
        """List all available plugins."""
        return self.plugin_manager.list_plugins(plugin_type)
    
    def get_pipeline_history(self, pipeline_id: str) -> List[Dict[str, Any]]:
        """Get execution history for a pipeline."""
        events = self.audit_logger.get_pipeline_events(pipeline_id)
        return [event.model_dump() for event in events]
    
    def get_recent_executions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent pipeline executions."""
        events = self.audit_logger.get_recent_events(limit)
        pipeline_events = [e for e in events if e.event_type == "pipeline_start"]
        return [event.model_dump() for event in pipeline_events]
