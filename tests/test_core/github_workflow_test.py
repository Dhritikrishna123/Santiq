"""Special test for GitHub Actions workflow compatibility."""

import pytest
import os
import subprocess
import sys
from pathlib import Path


class TestGitHubWorkflowCompatibility:
    """Tests specifically designed for GitHub Actions workflow."""
    
    def test_package_installation(self):
        """Test that the package can be installed in a clean environment."""
        # This test verifies that all dependencies are properly specified
        # and the package can be installed from the current directory
        
        # In GitHub Actions, this would be run after pip install -e .
        try:
            import santiq
            assert hasattr(santiq, '__version__')
        except ImportError:
            pytest.fail("Santiq package not properly installed")

    def test_cli_availability(self):
        """Test that CLI is available after installation."""
        result = subprocess.run([sys.executable, "-m", "santiq.cli.main", "--help"], 
                              capture_output=True, text=True)
        
        assert result.returncode == 0
        assert "Santiq" in result.stdout

    def test_basic_pipeline_execution_ci(self):
        """Test basic pipeline execution in CI environment."""
        import tempfile
        import pandas as pd
        from santiq.core.engine import ETLEngine
        from santiq.core.config import PipelineConfig
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create test data
            test_data = pd.DataFrame({
                "id": [1, 2, 3, 4],
                "name": ["Alice", "Bob", "Charlie", "Diana"]
            })
            
            input_path = temp_path / "input.csv"
            output_path = temp_path / "output.csv"
            
            test_data.to_csv(input_path, index=False)
            
            # Create minimal config
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
            
            # Execute pipeline
            engine = ETLEngine()
            result = engine.run_pipeline_from_config(config, mode="controlled-auto")
            
            assert result["success"] is True
            assert output_path.exists()
    
    def test_plugin_discovery_in_ci(self):
        """Test that built-in plugins are discovered in CI environment."""
        from santiq.core.plugin_manager import PluginManager
        
        plugin_manager = PluginManager()
        plugins = plugin_manager.discover_plugins()
        
        # Verify core plugins are available
        assert "extractor" in plugins
        assert len(plugins["extractor"]) > 0
        
        extractor_names = [p["name"] for p in plugins["extractor"]]
        assert "csv_extractor" in extractor_names
    
    def test_environment_variables_in_config(self):
        """Test environment variable substitution works in CI."""
        import os
        import tempfile
        import yaml
        from santiq.core.config import ConfigManager
        
        # Set test environment variables
        os.environ["CI_INPUT_PATH"] = "/test/input"
        os.environ["CI_OUTPUT_PATH"] = "/test/output"
        
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
                config_data = {
                    "extractor": {
                        "plugin": "csv_extractor",
                        "params": {"path": "${CI_INPUT_PATH}/data.csv"}
                    },
                    "loaders": [{
                        "plugin": "csv_loader",
                        "params": {"path": "${CI_OUTPUT_PATH}/result.csv"}
                    }]
                }
                yaml.dump(config_data, f)
                f.flush()
                
                config_manager = ConfigManager()
                pipeline_config = config_manager.load_pipeline_config(f.name)
                
                assert "/test/input/data.csv" in pipeline_config.extractor.params["path"]
                assert "/test/output/result.csv" in pipeline_config.loaders[0].params["path"]
        
        finally:
            # Clean up
            os.environ.pop("CI_INPUT_PATH", None)
            os.environ.pop("CI_OUTPUT_PATH", None)
            if 'f' in locals():
                os.unlink(f.name)