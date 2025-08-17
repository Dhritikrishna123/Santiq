"""Integration tests for complete pipeline execution."""

from pathlib import Path
from unittest.mock import Mock, patch

import pandas as pd
import pytest
import yaml

from santiq.core.config import PipelineConfig
from santiq.core.engine import ETLEngine


@pytest.mark.integration
class TestPipelineExecution:
    """Test complete pipeline execution scenarios."""

    def test_simple_pipeline_execution(self, temp_dir: Path, sample_data: pd.DataFrame):
        """Test simple pipeline execution."""
        # Create input file
        input_file = temp_dir / "input.csv"
        sample_data.to_csv(input_file, index=False)

        # Create output directory
        output_dir = temp_dir / "output"
        output_dir.mkdir()

        # Create pipeline config
        config = PipelineConfig(
            extractor={"plugin": "csv_extractor", "params": {"path": str(input_file)}},
            transformers=[
                {
                    "plugin": "basic_cleaner",
                    "params": {"drop_nulls": True, "drop_duplicates": True},
                }
            ],
            loaders=[
                {
                    "plugin": "csv_loader",
                    "params": {"path": str(output_dir / "output.csv")},
                }
            ],
        )

        # Run pipeline
        engine = ETLEngine()
        result = engine.run_pipeline_from_config(config)

        assert result["success"] is True
        assert "data" in result
        assert len(result["data"]) > 0

        # Check output file was created
        output_file = output_dir / "output.csv"
        assert output_file.exists()

    def test_pipeline_with_config_file(self, temp_dir: Path, sample_data: pd.DataFrame):
        """Test pipeline execution with config file."""
        # Create input file
        input_file = temp_dir / "input.csv"
        sample_data.to_csv(input_file, index=False)

        # Create output directory
        output_dir = temp_dir / "output"
        output_dir.mkdir()

        # Create config file
        config_file = temp_dir / "pipeline.yml"
        config_content = f"""
    extractor:
      plugin: csv_extractor
      params:
        path: {input_file}
    
    transformers:
      - plugin: basic_cleaner
        params:
          drop_nulls: true
          drop_duplicates: true
    
    loaders:
      - plugin: csv_loader
        params:
          path: {output_dir}/output.csv
    """

        with open(config_file, "w") as f:
            f.write(config_content)

        # Run pipeline from file
        engine = ETLEngine()
        result = engine.run_pipeline_from_file(str(config_file))

        assert result["success"] is True
        assert "data" in result

        # Check output file was created
        output_file = output_dir / "output.csv"
        assert output_file.exists()

    def test_pipeline_error_handling(self, temp_dir: Path):
        """Test pipeline error handling."""
        # Create config with nonexistent extractor plugin
        config = PipelineConfig(
            extractor={"plugin": "nonexistent_extractor", "params": {}},
            loaders=[
                {
                    "plugin": "csv_loader",
                    "params": {"path": str(temp_dir / "output.csv")},
                }
            ],
        )

        # Run pipeline - this should fail due to nonexistent plugin
        engine = ETLEngine()

        with pytest.raises(Exception):  # Should raise PluginNotFoundError or similar
            engine.run_pipeline_from_config(config)

    def test_pipeline_audit_logging(self, temp_dir: Path, sample_data: pd.DataFrame):
        """Test pipeline audit logging."""
        # Create input file
        input_file = temp_dir / "input.csv"
        sample_data.to_csv(input_file, index=False)

        # Create output directory
        output_dir = temp_dir / "output"
        output_dir.mkdir()

        # Create pipeline config
        config = PipelineConfig(
            extractor={"plugin": "csv_extractor", "params": {"path": str(input_file)}},
            loaders=[
                {
                    "plugin": "csv_loader",
                    "params": {"path": str(output_dir / "output.csv")},
                }
            ],
        )

        # Run pipeline
        engine = ETLEngine()
        result = engine.run_pipeline_from_config(config)

        assert result["success"] is True

        # Check audit log
        audit_log = engine.get_audit_log()
        assert len(audit_log) > 0

        # Check recent execution
        recent = engine.get_recent_executions()
        assert len(recent) > 0

    def test_pipeline_modes(self, temp_dir: Path, sample_data: pd.DataFrame):
        """Test different pipeline execution modes."""
        # Create input file
        input_file = temp_dir / "input.csv"
        sample_data.to_csv(input_file, index=False)

        # Create output directory
        output_dir = temp_dir / "output"
        output_dir.mkdir()

        # Create pipeline config
        config = PipelineConfig(
            extractor={"plugin": "csv_extractor", "params": {"path": str(input_file)}},
            loaders=[
                {
                    "plugin": "csv_loader",
                    "params": {"path": str(output_dir / "output.csv")},
                }
            ],
        )

        # Test controlled mode
        engine = ETLEngine()
        result = engine.run_pipeline_from_config(config, mode="controlled")

        assert result["success"] is True

        # Test controlled-auto mode
        result = engine.run_pipeline_from_config(config, mode="controlled-auto")

        assert result["success"] is True
