"""
Test suite for configuration manager module.
"""
import pytest
import tempfile
import json
import os
import shutil
from pathlib import Path
from unittest.mock import patch, mock_open, Mock

# Add the project root to sys.path for imports
import sys
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from redhat_status.config.config_manager import ConfigManager, get_config


class TestConfigManager:
    """Test the ConfigManager class"""
    
    def setup_method(self):
        """Set up test method"""
        self.temp_dir = tempfile.mkdtemp()
        self.config_file = os.path.join(self.temp_dir, 'test_config.json')
    
    def teardown_method(self):
        """Clean up after test"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_init_with_config_file(self):
        """Test initialization with a config file"""
        config_data = {
            'cache': {'enabled': True, 'ttl': 300},
            'api': {'timeout': 30}
        }
        
        with open(self.config_file, 'w') as f:
            json.dump(config_data, f)
        
        config = ConfigManager(config_file=self.config_file)
        
        assert config.get('cache', 'enabled') is True
        assert config.get('cache', 'ttl') == 300
        assert config.get('api', 'timeout') == 30
    
    def test_init_without_config_file(self):
        """Test initialization without a config file uses defaults"""
        config = ConfigManager()
        
        # Should have default values
        assert isinstance(config.config, dict)
        assert 'cache' in config.config
        assert 'api' in config.config
    
    def test_get_existing_value(self):
        """Test getting an existing configuration value"""
        config = ConfigManager()
        config.config = {
            'section': {'key': 'value'}
        }
        
        result = config.get('section', 'key')
        assert result == 'value'
    
    def test_get_nonexistent_section(self):
        """Test getting from a non-existent section returns default"""
        config = ConfigManager()
        
        result = config.get('nonexistent', 'key', 'default')
        assert result == 'default'
    
    def test_get_nonexistent_key(self):
        """Test getting a non-existent key returns default"""
        config = ConfigManager()
        config.config = {'section': {}}
        
        result = config.get('section', 'nonexistent', 'default')
        assert result == 'default'
    
    def test_set_value(self):
        """Test setting a configuration value"""
        config = ConfigManager()
        
        config.set('section', 'key', 'new_value')
        
        assert config.get('section', 'key') == 'new_value'
    
    def test_set_value_creates_section(self):
        """Test setting a value creates the section if it doesn't exist"""
        config = ConfigManager()
        config.config = {}
        
        config.set('new_section', 'key', 'value')
        
        assert config.get('new_section', 'key') == 'value'
    
    def test_validate_valid_config(self):
        """Test validation of a valid configuration"""
        config = ConfigManager()
        config.config = {
            'cache': {'enabled': True, 'ttl': 300},
            'api': {'timeout': 30, 'retries': 3},
            'database': {'enabled': False},
            'notifications': {
                'email': {'enabled': False},
                'webhooks': {'enabled': False}
            }
        }
        
        result = config.validate()
        
        assert result['valid'] is True
        assert len(result['errors']) == 0
    
    def test_validate_invalid_config(self):
        """Test validation of an invalid configuration"""
        config = ConfigManager()
        config.config = {
            'cache': {'ttl': 'invalid'},  # Should be integer
            'api': {'timeout': -1}  # Should be positive
        }
        
        result = config.validate()
        
        assert result['valid'] is False
        assert len(result['errors']) > 0
    
    def test_save_config(self):
        """Test saving configuration to file"""
        config = ConfigManager()
        config.config = {'test': {'key': 'value'}}
        
        config.save(self.config_file)
        
        # Verify file was created and contains correct data
        assert os.path.exists(self.config_file)
        with open(self.config_file, 'r') as f:
            saved_data = json.load(f)
        
        assert saved_data['test']['key'] == 'value'
    
    def test_load_invalid_json(self):
        """Test loading invalid JSON file"""
        with open(self.config_file, 'w') as f:
            f.write('invalid json content')
        
        config = ConfigManager(config_file=self.config_file)
        
        # Should fall back to defaults when JSON is invalid
        assert isinstance(config.config, dict)
    
    def test_load_nonexistent_file(self):
        """Test loading non-existent file"""
        nonexistent_file = os.path.join(self.temp_dir, 'nonexistent.json')
        
        config = ConfigManager(config_file=nonexistent_file)
        
        # Should use defaults when file doesn't exist
        assert isinstance(config.config, dict)
    
    @patch('builtins.open', mock_open())
    def test_save_permission_error(self):
        """Test handling permission error when saving"""
        config = ConfigManager()
        
        with patch('builtins.open', side_effect=PermissionError("Access denied")):
            # Should not raise exception
            config.save(self.config_file)
    
    def test_get_section(self):
        """Test getting an entire section"""
        config = ConfigManager()
        config.config = {
            'section': {'key1': 'value1', 'key2': 'value2'}
        }
        
        section = config.get_section('section')
        
        assert section == {'key1': 'value1', 'key2': 'value2'}
    
    def test_get_nonexistent_section_returns_empty_dict(self):
        """Test getting a non-existent section returns empty dict"""
        config = ConfigManager()
        
        section = config.get_section('nonexistent')
        
        assert section == {}
    
    def test_has_section(self):
        """Test checking if section exists"""
        config = ConfigManager()
        config.config = {'existing': {}}
        
        assert config.has_section('existing') is True
        assert config.has_section('nonexistent') is False
    
    def test_remove_section(self):
        """Test removing a section"""
        config = ConfigManager()
        config.config = {
            'section1': {'key': 'value'},
            'section2': {'key': 'value'}
        }
        
        config.remove_section('section1')
        
        assert 'section1' not in config.config
        assert 'section2' in config.config
    
    def test_remove_nonexistent_section(self):
        """Test removing a non-existent section doesn't raise error"""
        config = ConfigManager()
        config.config = {}
        
        # Should not raise exception
        config.remove_section('nonexistent')


class TestGetConfigFunction:
    """Test the get_config function"""
    
    def test_get_config_singleton(self):
        """Test that get_config returns the same instance"""
        config1 = get_config()
        config2 = get_config()
        
        assert config1 is config2
    
    @patch('redhat_status.config.config_manager.ConfigManager')
    def test_get_config_creates_instance(self, mock_config_manager):
        """Test that get_config creates a ConfigManager instance"""
        mock_instance = Mock()
        mock_config_manager.return_value = mock_instance
        
        # Clear any existing singleton
        import redhat_status.config.config_manager as config_module
        config_module._config_instance = None
        
        result = get_config()
        
        mock_config_manager.assert_called_once()
        assert result == mock_instance


class TestConfigValidation:
    """Test configuration validation logic"""
    
    def setup_method(self):
        """Set up test method"""
        self.config = ConfigManager()
    
    def test_validate_cache_config(self):
        """Test cache configuration validation"""
        # Valid cache config
        self.config.config = {
            'cache': {
                'enabled': True,
                'ttl': 300,
                'max_size': 100
            }
        }
        
        result = self.config.validate()
        assert result['valid'] is True
        
        # Invalid cache config
        self.config.config = {
            'cache': {
                'enabled': 'invalid',  # Should be boolean
                'ttl': -1,  # Should be positive
                'max_size': 'invalid'  # Should be integer
            }
        }
        
        result = self.config.validate()
        assert result['valid'] is False
        assert len(result['errors']) > 0
    
    def test_validate_api_config(self):
        """Test API configuration validation"""
        # Valid API config
        self.config.config = {
            'api': {
                'timeout': 30,
                'retries': 3,
                'base_url': 'https://status.redhat.com'
            }
        }
        
        result = self.config.validate()
        assert result['valid'] is True
        
        # Invalid API config
        self.config.config = {
            'api': {
                'timeout': -1,  # Should be positive
                'retries': 'invalid',  # Should be integer
                'base_url': 'invalid-url'  # Should be valid URL
            }
        }
        
        result = self.config.validate()
        assert result['valid'] is False
        assert len(result['errors']) > 0
    
    def test_validate_database_config(self):
        """Test database configuration validation"""
        # Valid database config
        self.config.config = {
            'database': {
                'enabled': True,
                'path': 'status.db',
                'cleanup_days': 30
            }
        }
        
        result = self.config.validate()
        assert result['valid'] is True
        
        # Invalid database config
        self.config.config = {
            'database': {
                'enabled': 'invalid',  # Should be boolean
                'cleanup_days': -1  # Should be positive
            }
        }
        
        result = self.config.validate()
        assert result['valid'] is False
        assert len(result['errors']) > 0
    
    def test_validate_notifications_config(self):
        """Test notifications configuration validation"""
        # Valid notifications config
        self.config.config = {
            'notifications': {
                'email': {
                    'enabled': True,
                    'smtp_server': 'smtp.example.com',
                    'smtp_port': 587,
                    'recipients': ['test@example.com']
                },
                'webhooks': {
                    'enabled': False
                }
            }
        }
        
        result = self.config.validate()
        assert result['valid'] is True
        
        # Invalid notifications config
        self.config.config = {
            'notifications': {
                'email': {
                    'enabled': True,
                    'smtp_port': 'invalid',  # Should be integer
                    'recipients': 'invalid'  # Should be list
                }
            }
        }
        
        result = self.config.validate()
        assert result['valid'] is False
        assert len(result['errors']) > 0


if __name__ == '__main__':
    pytest.main([__file__])
