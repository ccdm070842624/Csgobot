"""Configuration management for CS:GO Trading Bot"""
import os
import yaml
import json
from pathlib import Path
from typing import Any, Dict, Optional


class Config:
    """Configuration manager with support for YAML and JSON"""

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration

        Args:
            config_path: Path to config file (YAML or JSON)
        """
        self.config_path = config_path or self._find_config_file()
        self.config_data = self._load_config()

    def _find_config_file(self) -> str:
        """Find config file in standard locations"""
        search_paths = [
            'config.yaml',
            'config.yml',
            'config.json',
            os.path.expanduser('~/.csgo_bot/config.yaml'),
            '/etc/csgo_bot/config.yaml'
        ]

        for path in search_paths:
            if os.path.exists(path):
                return path

        # Return default if not found
        return 'config.yaml'

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file"""
        if not os.path.exists(self.config_path):
            print(f"⚠️  Config file not found: {self.config_path}")
            print("   Using default configuration")
            return self._get_default_config()

        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                if self.config_path.endswith('.json'):
                    return json.load(f)
                else:
                    return yaml.safe_load(f) or {}
        except Exception as e:
            print(f"⚠️  Error loading config: {e}")
            print("   Using default configuration")
            return self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            'api': {
                'csgofloat': {
                    'api_key': None,
                    'base_url': 'https://csgofloat.com/api/v1',
                    'timeout': 15,
                    'rate_limit_delay': 5,
                    'max_retries': 3,
                    'retry_delay': 2
                }
            },
            'database': {
                'name': 'csgo_prices.db'
            },
            'strategy': {
                'min_buy_confidence': 50,
                'trend_days': 7,
                'prediction_days_ahead': 7
            },
            'logging': {
                'level': 'INFO',
                'console_enabled': True
            }
        }

    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get configuration value by dot-separated path

        Args:
            key_path: Dot-separated path (e.g., 'api.csgofloat.api_key')
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        keys = key_path.split('.')
        value = self.config_data

        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default

        return value

    def set(self, key_path: str, value: Any) -> None:
        """
        Set configuration value by dot-separated path

        Args:
            key_path: Dot-separated path
            value: Value to set
        """
        keys = key_path.split('.')
        data = self.config_data

        for key in keys[:-1]:
            if key not in data or not isinstance(data[key], dict):
                data[key] = {}
            data = data[key]

        data[keys[-1]] = value

    def save(self, path: Optional[str] = None) -> None:
        """
        Save configuration to file

        Args:
            path: Path to save to (uses current config_path if None)
        """
        save_path = path or self.config_path

        try:
            # Create directory if needed
            os.makedirs(os.path.dirname(os.path.abspath(save_path)), exist_ok=True)

            with open(save_path, 'w', encoding='utf-8') as f:
                if save_path.endswith('.json'):
                    json.dump(self.config_data, f, indent=2)
                else:
                    yaml.dump(self.config_data, f, default_flow_style=False)

            print(f"✅ Configuration saved to {save_path}")
        except Exception as e:
            print(f"❌ Error saving config: {e}")

    # Convenient property accessors
    @property
    def api_key(self) -> Optional[str]:
        """Get CSGOFloat API key"""
        return self.get('api.csgofloat.api_key')

    @property
    def db_name(self) -> str:
        """Get database name"""
        return self.get('database.name', 'csgo_prices.db')

    @property
    def items_to_track(self) -> list:
        """Get list of items to track"""
        return self.get('items', [])

    @property
    def log_level(self) -> str:
        """Get logging level"""
        return self.get('logging.level', 'INFO')

    @property
    def trend_days(self) -> int:
        """Get trend analysis days"""
        return self.get('strategy.trend_days', 7)

    @property
    def prediction_days_ahead(self) -> int:
        """Get prediction horizon"""
        return self.get('strategy.prediction_days_ahead', 7)

    @property
    def min_buy_confidence(self) -> float:
        """Get minimum buy confidence threshold"""
        return self.get('strategy.min_buy_confidence', 50)

    def __repr__(self) -> str:
        return f"Config(path='{self.config_path}')"


# Global config instance
_global_config: Optional[Config] = None


def get_config(config_path: Optional[str] = None) -> Config:
    """
    Get global configuration instance

    Args:
        config_path: Path to config file (only used on first call)

    Returns:
        Global Config instance
    """
    global _global_config

    if _global_config is None:
        _global_config = Config(config_path)

    return _global_config


def reload_config(config_path: Optional[str] = None) -> Config:
    """
    Reload configuration from file

    Args:
        config_path: Path to config file

    Returns:
        New Config instance
    """
    global _global_config
    _global_config = Config(config_path)
    return _global_config
