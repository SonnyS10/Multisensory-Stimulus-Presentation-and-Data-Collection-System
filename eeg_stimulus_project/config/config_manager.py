"""
Configuration management for the EEG Stimulus Project.
This module handles loading and accessing configuration settings from settings.yaml.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
import logging

class ConfigManager:
    """
    Centralized configuration management for the EEG Stimulus Project.
    Loads settings from settings.yaml and provides easy access to configuration values.
    """
    
    _instance = None
    _config = None
    
    def __new__(cls):
        """Singleton pattern to ensure only one config manager exists."""
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize the configuration manager."""
        if self._config is None:
            self._load_config()
    
    def _load_config(self):
        """Load configuration from settings.yaml file."""
        try:
            # Get the project root directory
            project_root = self._get_project_root()
            config_path = project_root / "eeg_stimulus_project" / "config" / "settings.yaml"
            
            if not config_path.exists():
                raise FileNotFoundError(f"Configuration file not found: {config_path}")
            
            with open(config_path, 'r', encoding='utf-8') as f:
                self._config = yaml.safe_load(f)
                
            logging.info(f"Configuration loaded from {config_path}")
            
        except Exception as e:
            logging.error(f"Failed to load configuration: {e}")
            # Use default configuration if loading fails
            self._config = self._get_default_config()
    
    def _get_project_root(self) -> Path:
        """Get the project root directory."""
        # Try to find the project root by looking for setup.py or eeg_stimulus_project directory
        current_path = Path(__file__).parent
        
        while current_path != current_path.parent:
            if (current_path / "setup.py").exists() or (current_path / "eeg_stimulus_project").exists():
                return current_path
            current_path = current_path.parent
        
        # If not found, use the current directory
        return Path.cwd()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Return default configuration values."""
        return {
            "paths": {
                "data_directory": "eeg_stimulus_project/saved_data",
                "assets_directory": "eeg_stimulus_project/assets",
                "images_directory": "Images",
                "log_file": "app.log",
                "tactile_data_file": "eeg_stimulus_project/stimulus/tactile_box_code/received_data.txt"
            },
            "network": {
                "host_port": 9999,
                "labrecorder_port": 22345,
                "timeout": 30,
                "tactile_system": {
                    "host": "10.115.12.225",
                    "username": "benja",
                    "password": "neuro",
                    "data_port": 5006,
                    "venv_activate": "source ~/Desktop/bin/activate",
                    "script_path": "python ~/forcereadwithzero.py"
                }
            },
            "hardware": {
                "tactile": {
                    "threshold": 500,
                    "baseline_force": 0,
                    "rezero_time": 2,
                    "rezero_threshold": 50
                }
            }
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value using dot notation.
        
        Args:
            key: Configuration key in dot notation (e.g., 'network.host_port')
            default: Default value if key is not found
            
        Returns:
            Configuration value or default
        """
        try:
            keys = key.split('.')
            value = self._config
            
            for k in keys:
                value = value[k]
            
            return value
            
        except (KeyError, TypeError):
            return default
    
    def get_path(self, key: str, relative_to_project_root: bool = True) -> Path:
        """
        Get a path configuration value as a Path object.
        
        Args:
            key: Configuration key for the path
            relative_to_project_root: If True, make path relative to project root
            
        Returns:
            Path object
        """
        path_str = self.get(key)
        if path_str is None:
            raise ValueError(f"Path configuration key '{key}' not found")
        
        path = Path(path_str)
        
        if relative_to_project_root and not path.is_absolute():
            path = self._get_project_root() / path
        
        return path
    
    def get_absolute_path(self, key: str) -> Path:
        """
        Get an absolute path configuration value.
        
        Args:
            key: Configuration key for the path
            
        Returns:
            Absolute Path object
        """
        return self.get_path(key, relative_to_project_root=True).resolve()
    
    def set(self, key: str, value: Any):
        """
        Set a configuration value using dot notation.
        
        Args:
            key: Configuration key in dot notation
            value: Value to set
        """
        keys = key.split('.')
        config = self._config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    def reload(self):
        """Reload configuration from file."""
        self._config = None
        self._load_config()
    
    def save(self, config_path: Optional[Path] = None):
        """
        Save current configuration to file.
        
        Args:
            config_path: Path to save configuration to. If None, uses default path.
        """
        if config_path is None:
            config_path = self._get_project_root() / "eeg_stimulus_project" / "config" / "settings.yaml"
        
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(self._config, f, default_flow_style=False, indent=2)
            
            logging.info(f"Configuration saved to {config_path}")
            
        except Exception as e:
            logging.error(f"Failed to save configuration: {e}")
            raise


# Global configuration manager instance
config = ConfigManager()


def get_config() -> ConfigManager:
    """Get the global configuration manager instance."""
    return config