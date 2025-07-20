"""Tests for configuration management."""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch
from notion_cli.config import Config


class TestConfig:
    """Test Config class."""
    
    def test_load_defaults(self):
        """Test loading default configuration."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.yaml"
            config = Config(config_path)
            
            assert config.output_format == "json"
            assert config.color_output is True
            assert config.page_size == 100
    
    def test_load_from_env(self):
        """Test loading configuration from environment variables."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.yaml"
            
            with patch.dict("os.environ", {
                "NOTION_API_KEY": "env-test-key",
                "NOTION_OUTPUT_FORMAT": "yaml",
                "NOTION_COLOR_OUTPUT": "false",
                "NOTION_PAGE_SIZE": "50"
            }):
                config = Config(config_path)
                
                assert config.api_key == "env-test-key"
                assert config.output_format == "yaml"
                assert config.color_output is False
                assert config.page_size == 50
    
    def test_save_and_load(self):
        """Test saving and loading configuration."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.yaml"
            
            # Create and save config
            config = Config(config_path)
            config.set("api_key", "test-key")
            config.set("custom_value", "test")
            config.save()
            
            # Load config
            config2 = Config(config_path)
            assert config2.get("api_key") == "test-key"
            assert config2.get("custom_value") == "test"
    
    def test_get_with_default(self):
        """Test getting configuration with default value."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.yaml"
            config = Config(config_path)
            
            assert config.get("nonexistent") is None
            assert config.get("nonexistent", "default") == "default"