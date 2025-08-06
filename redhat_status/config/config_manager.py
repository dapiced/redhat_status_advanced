"""
Red Hat Status Checker - Configuration Manager

This module handles all configuration loading, validation, and management
for the Red Hat Status monitoring system. It provides:

- Configuration file loading with defaults
- Environment variable overrides
- Configuration validation and error handling
- Dynamic configuration updates

Author: Red Hat Status Checker v3.1.0 - Modular Edition
"""

import json
import os
import logging
from typing import Dict, Any, Optional
from pathlib import Path


class ConfigManager:
    """Configuration management for Red Hat Status Checker"""
    
    DEFAULT_CONFIG = {
        "api": {
            "url": "https://status.redhat.com/api/v2/summary.json",
            "timeout": 10,
            "max_retries": 3,
            "retry_delay": 2,
            "concurrent_requests": 1,
            "rate_limit_delay": 0.5
        },
        "output": {
            "default_directory": ".",
            "create_summary_report": True,
            "timestamp_format": "%Y%m%d_%H%M%S",
            "max_file_size_mb": 50,
            "compression": False
        },
        "display": {
            "show_percentages": True,
            "show_health_indicator": True,
            "show_group_summaries": True,
            "show_performance_metrics": False,
            "color_output": True,
            "progress_bars": False
        },
        "cache": {
            "enabled": True,
            "ttl": 300,  # 5 minutes
            "directory": ".cache",
            "max_size_mb": 100,
            "compression": True,
            "cleanup_interval": 3600  # 1 hour
        },
        "logging": {
            "enabled": False,
            "level": "INFO",
            "file": "redhat_status.log",
            "max_size_mb": 10,
            "backup_count": 5,
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        },
        "monitoring": {
            "enabled": False,
            "alert_thresholds": {
                "availability_critical": 85.0,
                "availability_warning": 95.0,
                "response_time_warning": 5.0,
                "error_rate_warning": 5.0
            },
            "health_check_interval": 300,
            "auto_recovery_attempts": 3
        },
        "performance": {
            "enable_metrics": True,
            "detailed_timing": False,
            "memory_profiling": False,
            "max_concurrent_operations": 5
        },
        "ai_analytics": {
            "enabled": True,
            "anomaly_detection": True,
            "predictive_analysis": True,
            "learning_window": 50,
            "anomaly_threshold": 2.0,
            "min_confidence": 0.7
        },
        "database": {
            "enabled": True,
            "path": "redhat_monitoring.db",
            "retention_days": 30,
            "auto_cleanup": True
        },
        "notifications": {
            "email": {
                "enabled": False,
                "smtp_server": "smtp.gmail.com",
                "smtp_port": 587,
                "use_tls": True,
                "from_address": "",
                "to_addresses": [],
                "username": "",
                "password": ""
            },
            "webhooks": {
                "enabled": False,
                "urls": []
            }
        },
        "slo": {
            "enabled": True,
            "targets": {
                "global_availability": 99.9,
                "response_time": 2.0,
                "uptime_monthly": 99.5
            },
            "tracking_period": "monthly",
            "alert_on_breach": True
        }
    }
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize configuration manager
        
        Args:
            config_path: Path to configuration file (default: config.json in script directory)
        """
        self.config_path = config_path or self._get_default_config_path()
        self._config = None
        self._load_config()
        self._apply_env_overrides()
    
    def _get_default_config_path(self) -> str:
        """Get default configuration file path"""
        # Look for config.json in the root directory (where the main script is)
        # Path structure: redhat_status/config/config_manager.py -> need to go up 2 levels
        root_dir = Path(__file__).parent.parent.parent
        return str(root_dir / 'config.json')
    
    def _load_config(self) -> None:
        """Load configuration from file or use defaults"""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                
                # Deep merge with defaults
                self._config = self._deep_merge(self.DEFAULT_CONFIG.copy(), user_config)
                logging.info(f"Configuration loaded from {self.config_path}")
                
            except Exception as e:
                logging.warning(f"Could not load config file ({e}), using defaults")
                self._config = self.DEFAULT_CONFIG.copy()
        else:
            logging.info(f"Config file {self.config_path} not found, using defaults")
            self._config = self.DEFAULT_CONFIG.copy()
    
    def _deep_merge(self, base: Dict[str, Any], update: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge two dictionaries"""
        for key, value in update.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                base[key] = self._deep_merge(base[key], value)
            else:
                base[key] = value
        return base
    
    def _apply_env_overrides(self) -> None:
        """Apply environment variable overrides"""
        # API configuration overrides
        if os.getenv('REDHAT_STATUS_API_URL'):
            self._config['api']['url'] = os.getenv('REDHAT_STATUS_API_URL')
        
        if os.getenv('REDHAT_STATUS_TIMEOUT'):
            try:
                self._config['api']['timeout'] = int(os.getenv('REDHAT_STATUS_TIMEOUT'))
            except ValueError:
                logging.warning("Invalid REDHAT_STATUS_TIMEOUT value, using config default")
        
        if os.getenv('REDHAT_STATUS_MAX_RETRIES'):
            try:
                self._config['api']['max_retries'] = int(os.getenv('REDHAT_STATUS_MAX_RETRIES'))
            except ValueError:
                logging.warning("Invalid REDHAT_STATUS_MAX_RETRIES value, using config default")
        
        if os.getenv('REDHAT_STATUS_RETRY_DELAY'):
            try:
                self._config['api']['retry_delay'] = int(os.getenv('REDHAT_STATUS_RETRY_DELAY'))
            except ValueError:
                logging.warning("Invalid REDHAT_STATUS_RETRY_DELAY value, using config default")
    
    def get(self, section: str, key: Optional[str] = None, default: Any = None) -> Any:
        """Get configuration value
        
        Args:
            section: Configuration section name
            key: Optional key within section
            default: Default value if not found
            
        Returns:
            Configuration value or default
        """
        if section not in self._config:
            return default
        
        if key is None:
            return self._config[section]
        
        return self._config[section].get(key, default)
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """Get entire configuration section
        
        Args:
            section: Section name
            
        Returns:
            Configuration section dictionary
        """
        return self._config.get(section, {})
    
    def set(self, section: str, key: str, value: Any) -> None:
        """Set configuration value
        
        Args:
            section: Configuration section name
            key: Key within section
            value: Value to set
        """
        if section not in self._config:
            self._config[section] = {}
        
        self._config[section][key] = value
    
    def validate(self) -> Dict[str, Any]:
        """Validate configuration and return validation results
        
        Returns:
            Dictionary with validation results
        """
        results = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        # Validate API configuration
        api_config = self.get_section('api')
        if not api_config.get('url'):
            results['errors'].append("API URL is required")
            results['valid'] = False
        
        if api_config.get('timeout', 0) <= 0:
            results['errors'].append("API timeout must be positive")
            results['valid'] = False
        
        # Validate email configuration if enabled
        email_config = self.get('notifications', 'email', {})
        if email_config.get('enabled', False):
            required_fields = ['smtp_server', 'from_address', 'to_addresses']
            for field in required_fields:
                if not email_config.get(field):
                    results['errors'].append(f"Email {field} is required when email notifications are enabled")
                    results['valid'] = False
        
        # Validate cache configuration
        cache_config = self.get_section('cache')
        if cache_config.get('enabled', True):
            if cache_config.get('ttl', 0) <= 0:
                results['warnings'].append("Cache TTL should be positive")
            
            if cache_config.get('max_size_mb', 0) <= 0:
                results['warnings'].append("Cache max size should be positive")
        
        return results
    
    def reload(self) -> bool:
        """Reload configuration from file
        
        Returns:
            True if reload successful, False otherwise
        """
        try:
            self._load_config()
            self._apply_env_overrides()
            logging.info("Configuration reloaded successfully")
            return True
        except Exception as e:
            logging.error(f"Failed to reload configuration: {e}")
            return False
    
    def save(self, path: Optional[str] = None) -> bool:
        """Save current configuration to file
        
        Args:
            path: Optional path to save to (default: current config path)
            
        Returns:
            True if save successful, False otherwise
        """
        save_path = path or self.config_path
        try:
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=2, ensure_ascii=False)
            logging.info(f"Configuration saved to {save_path}")
            return True
        except Exception as e:
            logging.error(f"Failed to save configuration: {e}")
            return False
    
    @property
    def config(self) -> Dict[str, Any]:
        """Get full configuration dictionary"""
        return self._config.copy()
    
    # Convenience properties for commonly used values
    @property
    def api_url(self) -> str:
        return self.get('api', 'url')
    
    @property
    def api_timeout(self) -> int:
        return self.get('api', 'timeout')
    
    @property
    def max_retries(self) -> int:
        return self.get('api', 'max_retries')
    
    @property
    def retry_delay(self) -> int:
        return self.get('api', 'retry_delay')
    
    @property
    def cache_enabled(self) -> bool:
        return self.get('cache', 'enabled', True)
    
    @property
    def cache_ttl(self) -> int:
        return self.get('cache', 'ttl', 300)


# Global configuration instance
config_manager = ConfigManager()


def get_config() -> ConfigManager:
    """Get global configuration manager instance"""
    return config_manager


def reload_config() -> bool:
    """Reload configuration from file"""
    return config_manager.reload()
