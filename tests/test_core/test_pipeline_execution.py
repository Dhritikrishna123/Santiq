"""Integration tests for complete pipeline execution."""

import pytest
import pandas as pd
from pathlib import Path
import yaml

from santiq.core.engine import ETLEngine
from santiq.core.config import PipelineConfig


class TestPipelineExecution:
    """Test complete pipeline execution scenarios."""
    
    def test_simple_pipeline_execution(self, temp_dir: Path, sample_data: pd.DataFrame):
        """Test execution of a simple CSV-to-CSV pipeline."""
        # Setup input and output paths
        input_path = temp_dir / "input.csv"
        output_path = temp_dir / "output.csv"
        
        # Save sample data
        sample_data.to_csv(input_path, index=False)
        
        # Create pipeline config
        config = PipelineConfig(
            name="test_pipeline",
            extractor={
                "plugin": "csv_extractor",
                "params": {"path": str(input_path)}
            },
            profilers=[{
                "plugin": "basic_profiler",
                "params": {}
            }],
            transformers=[{
                "plugin": "basic_cleaner",
                "params": {
                    "drop_nulls": True,
                    "drop_duplicates": True
                }
            }],
            loaders=[{
                "plugin": "csv_loader",
                "params": {"path": str(output_path)}
            }]
        )
        
        # Execute pipeline
        engine = ETLEngine()
        result = engine.run_pipeline_from_config(config, mode="controlled-auto")
        
        # Verify results
        assert result["success"] is True
        assert result["rows_processed"] > 0
        assert output_path.exists()
        
        # Check output data quality
        output_data = pd.read_csv(output_path)
        assert len(output_data) <= len(sample_data)  # Some rows may have been cleaned
        assert output_data.isnull().sum().sum() == 0  # No nulls should remain
    
    def test_pipeline_with_config_file(self, temp_dir: Path, sample_data: pd.DataFrame):
        """Test pipeline execution from configuration file."""
        # Setup files
        input_path = temp_dir / "input.csv"
        output_path = temp_dir / "output.csv"
        config_path = temp_dir / "pipeline.yml"
        
        sample_data.to_csv(input_path, index=False)
        
        # Create config file
        config_data = {
            "name": "file_based_pipeline",
            "description": "Pipeline loaded from file",
            "extractor": {
                "plugin": "csv_extractor",
                "params": {"path": str(input_path)}
            },
            "profilers": [{
                "plugin": "basic_profiler"
            }],
            "transformers": [{
                "plugin": "basic_cleaner",
                "params": {
                    "drop_nulls": True,
                    "drop_duplicates": True
                }
            }],
            "loaders": [{
                "plugin": "csv_loader",
                "params": {"path": str(output_path)}
            }]
        }
        
        with open(config_path, 'w') as f:
            yaml.dump(config_data, f)
        
        # Execute pipeline
        engine = ETLEngine()
        result = engine.run_pipeline(str(config_path), mode="controlled-auto")
        
        assert result["success"] is True
        assert output_path.exists()
    
    def test_pipeline_error_handling(self, temp_dir: Path):
        """Test pipeline error handling."""
        # Create config with non-existent input file
        config = PipelineConfig(
            extractor={
                "plugin": "csv_extractor",
                "params": {"path": "/nonexistent/file.csv"}
            },
            loaders=[{
                "plugin": "csv_loader",
                "params": {"path": str(temp_dir / "output.csv")}
            }]
        )
        
        engine = ETLEngine()
        
        with pytest.raises(Exception):  # Should raise pipeline execution error
            engine.run_pipeline_from_config(config)
    
    def test_pipeline_audit_logging(self, temp_dir: Path, sample_data: pd.DataFrame):
        """Test that pipeline execution is properly audited."""
        input_path = temp_dir / "input.csv"
        output_path = temp_dir / "output.csv"
        audit_path = temp_dir / "audit.jsonl"
        
        sample_data.to_csv(input_path, index=False)
        
        config = PipelineConfig(
            extractor={
                "plugin": "csv_extractor",
                "params": {"path": str(input_path)}
            },
            loaders=[{
                "plugin": "csv_loader",
                "params": {"path": str(output_path)}
            }]
        )
        
        # Execute with specific audit file
        engine = ETLEngine(audit_log_file=str(audit_path))
        result = engine.run_pipeline_from_config(config)
        
        # Check audit logging
        assert audit_path.exists()
        
        pipeline_id = result["pipeline_id"]
        history = engine.get_pipeline_history(pipeline_id)
        
        assert len(history) > 0
        event_types = {event["event_type"] for event in history}
        assert "pipeline_start" in event_types
        assert "pipeline_complete" in event_types or "pipeline_error" in event_types
    
    def test_pipeline_modes(self, temp_dir: Path, sample_data: pd.DataFrame):
        """Test different pipeline execution modes."""
        input_path = temp_dir / "input.csv"
        output_path = temp_dir / "output.csv"
        
        sample_data.to_csv(input_path, index=False)
        
        config = PipelineConfig(
            extractor={
                "plugin": "csv_extractor", 
                "params": {"path": str(input_path)}
            },
            profilers=[{
                "plugin": "basic_profiler"
            }],
            transformers=[{
                "plugin": "basic_cleaner",
                "params": {"drop_nulls": True}
            }],
            loaders=[{
                "plugin": "csv_loader",
                "params": {"path": str(output_path)}
            }]
        )
        
        engine = ETLEngine()
        
        # Test different modes
        for mode in ["manual", "half-auto", "controlled-auto"]:
            if output_path.exists():
                output_path.unlink()
            
            result = engine.run_pipeline_from_config(config, mode=mode)
            
            assert result["success"] is True
            assert output_path.exists()
