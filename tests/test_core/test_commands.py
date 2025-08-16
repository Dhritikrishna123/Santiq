"""Tests for CLI commands."""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from typer.testing import CliRunner

from santiq.cli.main import app


class TestCLICommands:
    """Test CLI command functionality."""
    
    def setUp(self):
        self.runner = CliRunner()
    
    def test_version_command(self):
        """Test version command."""
        runner = CliRunner()
        result = runner.invoke(app, ["version"])
        
        assert result.exit_code == 0
        assert "santiq version" in result.stdout
    
    def test_init_command(self):
        """Test pipeline initialization command."""
        runner = CliRunner()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            with runner.isolated_filesystem(temp_dir):
                result = runner.invoke(app, ["init", "test_pipeline"])
                
                assert result.exit_code == 0
                assert "Created pipeline config" in result.stdout
                
                # Check that config file was created
                config_file = Path("test_pipeline.yml")
                assert config_file.exists()
                
                # Check content
                content = config_file.read_text()
                assert "name: test_pipeline" in content
                assert "csv_extractor" in content
    
    def test_init_existing_file(self):
        """Test init command with existing file."""
        runner = CliRunner()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            with runner.isolated_filesystem(temp_dir):
                # Create existing file
                Path("existing.yml").write_text("existing content")
                
                result = runner.invoke(app, ["init", "existing"])
                
                assert result.exit_code == 1
                assert "already exists" in result.stdout
    
    @patch('santiq.core.engine.ETLEngine.run_pipeline')
    def test_run_pipeline_command(self, mock_run):
        """Test running pipeline from CLI."""
        mock_run.return_value = {
            "success": True,
            "pipeline_id": "test-123",
            "rows_processed": 100,
            "fixes_applied": []
        }
        
        runner = CliRunner()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = Path(temp_dir) / "pipeline.yml"
            config_file.write_text("extractor:\n  plugin: csv_extractor\nloaders:\n  - plugin: csv_loader")
            
            result = runner.invoke(app, ["run", "pipeline", str(config_file)])
            
            assert result.exit_code == 0
            assert "Pipeline completed successfully" in result.stdout
            assert mock_run.called
    
    def test_plugin_list_command(self):
        """Test plugin list command."""
        runner = CliRunner()
        result = runner.invoke(app, ["plugin", "list"])
        
        assert result.exit_code == 0
        # Should show plugin categories
        assert any(word in result.stdout.lower() for word in ["extractor", "loader", "profiler", "transformer"])
    
    @patch('subprocess.run')
    def test_plugin_install_command(self, mock_subprocess):
        """Test plugin installation command."""
        mock_subprocess.return_value = Mock(stdout="Successfully installed", stderr="", returncode=0)
        
        runner = CliRunner()
        result = runner.invoke(app, ["plugin", "install", "test-plugin", "--dry-run"])
        
        assert result.exit_code == 0
        assert "Would run" in result.stdout
