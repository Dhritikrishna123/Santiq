"""Configuration management for the Santiq platform."""

import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional
import yaml
from pydantic import BaseModel, Field, field_validator

from santiq.core.exceptions import PipelineConfigError

class PluginConfig(BaseModel):
    """Configuration for a single plugin"""
    plugin: str
    params: Dict[str, Any] = Field(default_factory=dict)
    on_error: str = Field(default="stop", regex="^(stop|continue|retry)$")
    enable: bool = True
    
class PipelineConfig(BaseModel):
    """Configuration for a data processing pipeline"""
    name: Optional[str] = None
    description: Optional[str] = None

    extractor: PluginConfig
    profilers: List[PluginConfig] = Field(default_factory=list)
    transformers: List[PluginConfig] = Field(default_factory=list)
    loaders: List[PluginConfig] 
    
    # Global settings
    cache_intermediate_results: bool = Field(default=True)
    max_memory_mb: Optional[int] = None
    temp_dir: Optional[str] = None
    
    @field_validator('loaders')
    def validate_loaders_not_empty(cls, v: List[PluginConfig]) -> List[PluginConfig]:
        if not v:
            raise ValueError('At least one loader must be specified')
        return v
    
    @field_validator('temp_dir')
    def validate_temp_dir(cls, v: Optional[str]) -> Optional[str]:
        if v and not Path(v).is_dir():
            raise ValueError('Temporary directory must be a valid directory path')
        return v

    @field_validator('max_memory_mb')
    def validate_max_memory_mb(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and v <= 0:
            raise ValueError('Max memory must be positive')
        return v

    @field_validator('cache_intermediate_results')
    def validate_cache_intermediate_results(cls, v: bool) -> bool:
        if not isinstance(v, bool):
            raise ValueError('Cache intermediate results must be a boolean')
        return v
    
class ConfigManager:
    """Manages Configuration loading and environment variable substitution"""

    def __init__(self):
        self.pattern = re.compile(r'\$\{([^}]+)\}')
        
    def load_pipeline_config(self, config_path: str)-> PipelineConfig:
        """Load and Validate pipeline Configuration from File"""
        config_file = Path(config_path)
        if not config_file.exists():
            PipelineConfigError(f"Configuration File Not Found: {config_path}")
            
        try:
            with open(config_file) as f:
                raw_config = yaml.safe_load(f)
                
            # Substitute Environmental Variable
            processed_config = self._substitute_env_vars_(raw_config)
            
            # Validate and create config object
            return PipelineConfig(**processed_config)
        
        except yaml.YAMLError as e:
            raise PipelineConfigError(f"Error parsing configuration file {config_path}: {e}")
        except Exception as e:
            raise PipelineConfigError(f"Unexpected error occurred while loading configuration file {config_path}: {e}")


    def _substitute_env_vars_(self, obj: Any) -> Any:
        """Recursively substitute environment variables in the config dictionary."""
        if isinstance(obj, dict):
            return {key: self._substitute_env_vars(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._substitute_env_vars(item) for item in obj]
        elif isinstance(obj, str):
            return self._substitute_string_env_vars(obj)
        else:
            return obj

    def _substitute_string_env_vars(self, text: str) -> str:
        """Substitute environment variables in a string."""
        def replace_var(match: re.Match[str]) -> str:
            var_name = match.group(1)
            default_value = ""  # Provide a default value if needed
            
            # Support ${VAR:default} syntax
            if ":" in var_name:
                var_name, default_value = var_name.split(":", 1)
            
            return os.getenv(var_name, default_value)

        return self.env_pattern.sub(replace_var, text)

    def save_preference(self, preference: Dict[str, Any], preference_file: Optional[str]=None) -> None:
        """Save a user preference to file"""
        if preference_file is None:
            preference_file = self._get_default_preference_file()

        preference_path = Path(preference_file)
        preference_path.parent.mkdir(parents=True, exist_ok=True)

        with open(preference_path, 'w') as f:
            yaml.dump(preference, f, default_flow_style=False)
            
    def load_preference(self, preference_file: Optional[str]=None) -> Dict[str, Any]:
        """Load user preference from file"""
        if preference_file is None:
            preference_file = self._get_default_preference_file()

        preference_path = Path(preference_file)
        if not preference_path.exists():
            return {}

        try:    
            with open(preference_path, 'r') as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            return {"error": str(e)}
        
    def _get_default_preference_file(self) -> str:
        if os.name == 'nt':  # Windows
            config_dir = os.getenv('APPDATA', os.path.expanduser('~'))
        else:  # Unix-like
            config_dir = os.getenv('XDG_CONFIG_HOME', os.path.expanduser('~/.config'))
        
        return os.path.join(config_dir, 'etl-core', 'preferences.yml')