"""Tests for configuration management."""

import unittest
import tempfile
import os
from pathlib import Path
import yaml

import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from utils.config import Config, reset_config


class TestConfig(unittest.TestCase):
    """Test suite for configuration management."""
    
    def setUp(self):
        """Create temporary config file for testing."""
        self.temp_config = tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False)
        self.config_path = self.temp_config.name
        
        # Write test config
        test_data = {
            'engine': {
                'target_hz': 60,
                'max_depth': 10
            },
            'gui': {
                'theme': 'light',
                'window_width': 1600
            },
            'test_value': 'hello'
        }
        
        yaml.dump(test_data, self.temp_config)
        self.temp_config.close()
        
        # Reset global config
        reset_config()
    
    def tearDown(self):
        """Clean up temporary files."""
        if os.path.exists(self.config_path):
            os.remove(self.config_path)
        reset_config()
    
    def test_load_from_file(self):
        """Test loading configuration from file."""
        config = Config(self.config_path)
        
        self.assertEqual(config.get('engine.target_hz'), 60)
        self.assertEqual(config.get('gui.theme'), 'light')
        self.assertEqual(config.get('test_value'), 'hello')
    
    def test_nested_get(self):
        """Test getting nested configuration values."""
        config = Config(self.config_path)
        
        self.assertEqual(config.get('engine.target_hz'), 60)
        self.assertEqual(config.get('engine.max_depth'), 10)
        self.assertEqual(config.get('gui.window_width'), 1600)
    
    def test_default_value(self):
        """Test default value when key doesn't exist."""
        config = Config(self.config_path)
        
        self.assertEqual(config.get('nonexistent.key', default=42), 42)
        self.assertIsNone(config.get('another.missing.key'))
    
    def test_set_value(self):
        """Test setting configuration values."""
        config = Config(self.config_path)
        
        config.set('engine.target_hz', 120)
        self.assertEqual(config.get('engine.target_hz'), 120)
        
        config.set('new.nested.value', 'test')
        self.assertEqual(config.get('new.nested.value'), 'test')
    
    def test_save_config(self):
        """Test saving configuration to file."""
        config = Config(self.config_path)
        
        config.set('engine.target_hz', 90)
        config.save()
        
        # Load again to verify
        new_config = Config(self.config_path)
        self.assertEqual(new_config.get('engine.target_hz'), 90)
    
    def test_default_config(self):
        """Test default configuration when file doesn't exist."""
        # Create config without file
        config = Config('/tmp/nonexistent_config_test.yaml')
        
        # Should still work with defaults
        target_hz = config.get('engine.target_hz', default=30)
        self.assertEqual(target_hz, 30)
    
    def test_reload(self):
        """Test reloading configuration from file."""
        config = Config(self.config_path)
        
        original_hz = config.get('engine.target_hz')
        self.assertEqual(original_hz, 60)
        
        # Modify file externally
        with open(self.config_path, 'r') as f:
            data = yaml.safe_load(f)
        data['engine']['target_hz'] = 45
        with open(self.config_path, 'w') as f:
            yaml.dump(data, f)
        
        # Reload
        config.reload()
        
        new_hz = config.get('engine.target_hz')
        self.assertEqual(new_hz, 45)


if __name__ == '__main__':
    unittest.main()
