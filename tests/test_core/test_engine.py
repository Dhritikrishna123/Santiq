"""Tests for ETL engine functionality."""

import pytest
from unittest.mock import Mock, patch
import uuid
from pathlib import Path

from santiq.core.engine import ETLEngine
from santiq.core.config import PipelineConfig
from santiq.core.exceptions import PipelineConfigError


class TestETLEngine:
    """Test ETL engine functionality."""
    
    def test_engine_initialization(self, temp_dir):
        """Test ETL engine initialization."""
        engine = ETLEngine(
            local_plugin_dirs=[str(temp_dir)],
            audit_log_file=str(temp_dir / "audit.log")
        )
        
        assert engine.plugin_manager is not None
        assert engine.audit_logger is not None
        assert engine.config_manager is not None
        assert engine.pipeline is not None
    
    def test_list_plugins(self, etl_engine: ETLEngine):
        """Test listing available plugins."""
        plugins = etl_engine.list_plugins()
        
        assert isinstance(plugins, dict)
        assert "extractor" in plugins
        assert "profiler" in plugins
        assert "transformer" in plugins
        assert "loader" in plugins
    
    def test_list_plugins_by_type(self, etl_engine: ETLEngine):
        """Test listing plugins filtered by type."""
        extractors = etl_engine.list_plugins("extractor")
        
        assert "extractor" in extractors
        assert "profiler" not in extractors
        assert "transformer" not in extractors
        assert "loader" not in extractors
    
    @patch('etl.core.engine.ETLEngine.run_pipeline_from_config')
    def test_run_pipeline_from_file(self, mock_run, temp_dir: Path, etl_engine: ETLEngine):
        """Test running pipeline from configuration file."""
        # Create a config file
        config_data = {
            "extractor": {"plugin": "csv_extractor", "params": {"path": "/test.csv"}},
            "loaders": [{"plugin": "csv_loader", "params": {"path": "/output.csv"}}]
        }
        
        config_file = temp_dir / "pipeline.yml"
        with open(config_file, 'w') as f:
            import yaml
            yaml.dump(config_data, f)
        
        mock_run.return_value = {"success": True, "pipeline_id": "test-123"}
        
        result = etl_engine.run_pipeline(str(config_file), mode="manual")
        
        assert mock_run.called
        assert result["success"] is True
    
    def test_pipeline_history_tracking(self, etl_engine: ETLEngine):
        """Test that pipeline history is tracked."""
        pipeline_id = str(uuid.uuid4())
        
        # Log some test events
        etl_engine.audit_logger.log_event("pipeline_start", pipeline_id)
        etl_engine.audit_logger.log_event("pipeline_complete", pipeline_id)
        
        history = etl_engine.get_pipeline_history(pipeline_id)
        
        assert len(history) == 2
        assert all(event["pipeline_id"] == pipeline_id for event in history)
    
    def test_recent_executions(self, etl_engine: ETLEngine):
        """Test getting recent pipeline executions."""
        # Log some pipeline starts
        for i in range(5):
            pipeline_id = str(uuid.uuid4())
            etl_engine.audit_logger.log_event("pipeline_start", pipeline_id)
        
        recent = etl_engine.get_recent_executions(limit=3)
        
        assert len(recent) <= 3
        assert all(event["event_type"] == "pipeline_start" for event in recent)