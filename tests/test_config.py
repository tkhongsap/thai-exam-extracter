"""Tests for Config class."""

import os
import tempfile
import pytest
import yaml
from pathlib import Path
import sys

# Add parent directory to path to import exam_extractor
sys.path.insert(0, str(Path(__file__).parent.parent))
from exam_extractor import Config, ConfigurationError


class TestConfig:
    """Test cases for Config class."""

    def test_default_config_when_file_not_found(self, tmp_path):
        """Test that default config is used when file is not found."""
        non_existent_file = tmp_path / "nonexistent.yaml"
        config = Config(config_file=str(non_existent_file))

        assert config.get('api.base_url') is not None
        assert config.get('api.timeout') == 30
        assert config.get('download.concurrent_limit') == 5

    def test_load_config_from_yaml(self, tmp_path):
        """Test loading configuration from YAML file."""
        config_file = tmp_path / "test_config.yaml"
        config_data = {
            'api': {
                'base_url': 'https://test.example.com',
                'timeout': 60,
                'max_retries': 5,
                'retry_delay': 3
            },
            'download': {
                'concurrent_limit': 10,
                'rate_limit_delay': 1.0,
                'resume': False
            }
        }

        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)

        config = Config(config_file=str(config_file))

        assert config.get('api.base_url') == 'https://test.example.com'
        assert config.get('api.timeout') == 60
        assert config.get('download.concurrent_limit') == 10

    def test_get_nested_config_value(self):
        """Test getting nested configuration values."""
        config = Config()

        # Test nested access
        base_url = config.get('api.base_url')
        assert base_url is not None
        assert isinstance(base_url, str)

        # Test default value
        non_existent = config.get('non.existent.key', 'default')
        assert non_existent == 'default'

    def test_env_override_api_base_url(self, monkeypatch, tmp_path):
        """Test that environment variables override config values."""
        config_file = tmp_path / "test_config.yaml"
        config_data = {
            'api': {
                'base_url': 'https://original.example.com',
                'timeout': 30
            }
        }

        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)

        # Set environment variable
        monkeypatch.setenv('EXAM_API_BASE_URL', 'https://override.example.com')

        config = Config(config_file=str(config_file))

        # Environment variable should override config file
        assert config.get('api.base_url') == 'https://override.example.com'

    def test_env_override_numeric_values(self, monkeypatch, tmp_path):
        """Test that numeric environment variables are properly converted."""
        config_file = tmp_path / "test_config.yaml"
        config_data = {
            'api': {'timeout': 30, 'max_retries': 3},
            'download': {'concurrent_limit': 5}
        }

        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)

        # Set environment variables
        monkeypatch.setenv('EXAM_API_TIMEOUT', '60')
        monkeypatch.setenv('EXAM_API_MAX_RETRIES', '10')
        monkeypatch.setenv('EXAM_CONCURRENT_LIMIT', '20')

        config = Config(config_file=str(config_file))

        assert config.get('api.timeout') == 60
        assert config.get('api.max_retries') == 10
        assert config.get('download.concurrent_limit') == 20

    def test_env_override_extraction_range(self, monkeypatch):
        """Test environment variable override for extraction range."""
        monkeypatch.setenv('EXAM_START_ID', '1000')
        monkeypatch.setenv('EXAM_END_ID', '2000')

        config = Config()

        assert config.get('extraction.start_id') == 1000
        assert config.get('extraction.end_id') == 2000
