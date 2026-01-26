"""Configuration management for PixelPilot.

This module provides a centralized configuration system using YAML files.
Supports nested key access, default values, and environment-specific overrides.
"""

import os
import yaml
from typing import Any, Optional, Dict
from pathlib import Path


class Config:
    """
    Configuration manager for PixelPilot.
    
    Loads configuration from YAML files and provides convenient access
    to nested configuration values with dot notation.
    
    Attributes:
        data (Dict[str, Any]): Loaded configuration dictionary
        config_path (Path): Path to the configuration file
        
    Example:
        >>> config = Config()
        >>> target_hz = config.get('engine.target_hz', default=30)
        >>> theme = config.get('gui.theme', default='dark')
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration manager.
        
        Args:
            config_path: Path to configuration file. If None, searches for
                        config.yaml in project root and current directory.
        """
        self.config_path = self._find_config_file(config_path)
        self.data: Dict[str, Any] = {}
        self._load_config()
    
    def _find_config_file(self, config_path: Optional[str]) -> Path:
        """
        Find configuration file in standard locations.
        
        Search order:
        1. Provided config_path
        2. PIXELPILOT_CONFIG environment variable
        3. ./config.yaml (current directory)
        4. Project root config.yaml
        
        Args:
            config_path: Optional explicit path
            
        Returns:
            Path to configuration file
            
        Raises:
            FileNotFoundError: If no configuration file found
        """
        if config_path:
            path = Path(config_path)
            if path.exists():
                return path
        
        # Check environment variable
        env_config = os.getenv('PIXELPILOT_CONFIG')
        if env_config:
            path = Path(env_config)
            if path.exists():
                return path
        
        # Check current directory
        current_dir_config = Path.cwd() / 'config.yaml'
        if current_dir_config.exists():
            return current_dir_config
        
        # Check project root (assuming structure: project_root/src/utils/config.py)
        project_root = Path(__file__).parent.parent.parent
        root_config = project_root / 'config.yaml'
        if root_config.exists():
            return root_config
        
        # Return default path (will create if needed)
        return root_config
    
    def _load_config(self) -> None:
        """
        Load configuration from YAML file.
        
        Creates default configuration if file doesn't exist.
        """
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    self.data = yaml.safe_load(f) or {}
            else:
                # Use default configuration
                self.data = self._get_default_config()
                # Optionally create config file
                # self._create_default_config()
        except yaml.YAMLError as e:
            raise ValueError(f"Error parsing config file {self.config_path}: {e}")
        except Exception as e:
            raise RuntimeError(f"Error loading config file {self.config_path}: {e}")
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation.
        
        Args:
            key_path: Dot-separated path to configuration key (e.g., 'engine.target_hz')
            default: Default value if key not found
            
        Returns:
            Configuration value or default
            
        Example:
            >>> config.get('engine.target_hz', default=30)
            30
            >>> config.get('gui.theme', default='dark')
            'dark'
        """
        keys = key_path.split('.')
        value = self.data
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def set(self, key_path: str, value: Any) -> None:
        """
        Set configuration value using dot notation.
        
        Args:
            key_path: Dot-separated path to configuration key
            value: Value to set
            
        Example:
            >>> config.set('engine.target_hz', 60)
            >>> config.set('gui.theme', 'light')
        """
        keys = key_path.split('.')
        data = self.data
        
        # Navigate to the parent key
        for key in keys[:-1]:
            if key not in data:
                data[key] = {}
            data = data[key]
        
        # Set the value
        data[keys[-1]] = value
    
    def save(self, path: Optional[str] = None) -> None:
        """
        Save configuration to YAML file.
        
        Args:
            path: Optional different path to save to. If None, saves to config_path.
        """
        save_path = Path(path) if path else self.config_path
        
        # Create parent directory if needed
        save_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(save_path, 'w') as f:
            yaml.safe_dump(self.data, f, default_flow_style=False, indent=2)
    
    def reload(self) -> None:
        """Reload configuration from file."""
        self._load_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """
        Get default configuration when no file exists.
        
        Returns:
            Default configuration dictionary
        """
        return {
            'engine': {
                'target_hz': 30,
                'max_depth': 5,
                'thread_safe': True
            },
            'graph': {
                'execution_passes': 3,
                'cycle_detection': True,
                'max_nodes': 1000
            },
            'vision': {
                'default_tolerance': 10,
                'cli_timeout': 5.0,
                'cache_screenshots': False
            },
            'input': {
                'evdev_priority': True,
                'listener_enabled': True,
                'key_repeat_delay': 0.1
            },
            'gui': {
                'theme': 'dark',
                'window_width': 1200,
                'window_height': 800,
                'autosave_interval': 300,
                'recent_files_count': 10
            },
            'logging': {
                'level': 'INFO',
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                'console': True,
                'file': False,
                'file_path': 'pixelpilot.log'
            },
            'paths': {
                'default_workspace': '~/PixelPilot/workflows',
                'templates': '~/PixelPilot/templates',
                'plugins': '~/PixelPilot/plugins'
            }
        }
    
    def _create_default_config(self) -> None:
        """Create default configuration file."""
        self.data = self._get_default_config()
        self.save()


# Global configuration instance (singleton pattern)
_global_config: Optional[Config] = None


def get_config() -> Config:
    """
    Get global configuration instance.
    
    Returns:
        Global Config instance
        
    Example:
        >>> from src.utils.config import get_config
        >>> config = get_config()
        >>> hz = config.get('engine.target_hz')
    """
    global _global_config
    if _global_config is None:
        _global_config = Config()
    return _global_config


def reset_config() -> None:
    """Reset global configuration instance (mainly for testing)."""
    global _global_config
    _global_config = None
