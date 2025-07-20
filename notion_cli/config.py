"""Configuration management for Notion CLI."""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load .env file if it exists
load_dotenv()


class Config:
    """Configuration manager for Notion CLI."""
    
    DEFAULT_CONFIG_DIR = Path.home() / ".notion-cli"
    DEFAULT_CONFIG_FILE = "config.yaml"
    
    def __init__(self, config_path: Optional[Path] = None):
        """Initialize configuration.
        
        Args:
            config_path: Optional path to config file. If not provided,
                        will use default location.
        """
        self.config_dir = self.DEFAULT_CONFIG_DIR
        self.config_path = config_path or (self.config_dir / self.DEFAULT_CONFIG_FILE)
        self._config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file and environment."""
        config = {}
        
        # Load from config file if it exists
        if self.config_path.exists():
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f) or {}
        
        # Override with environment variables
        env_mapping = {
            "NOTION_API_KEY": "api_key",
            "NOTION_DEFAULT_DATABASE": "default_database",
            "NOTION_OUTPUT_FORMAT": "output_format",
            "NOTION_COLOR_OUTPUT": "color_output",
            "NOTION_PAGE_SIZE": "page_size",
        }
        
        for env_var, config_key in env_mapping.items():
            value = os.getenv(env_var)
            if value:
                # Handle boolean conversion
                if config_key in ["color_output"]:
                    config[config_key] = value.lower() in ["true", "1", "yes"]
                # Handle integer conversion
                elif config_key in ["page_size"]:
                    try:
                        config[config_key] = int(value)
                    except ValueError:
                        pass
                else:
                    config[config_key] = value
        
        # Set defaults
        defaults = {
            "output_format": "json",
            "color_output": True,
            "page_size": 100,
        }
        
        for key, default_value in defaults.items():
            if key not in config:
                config[key] = default_value
        
        return config
    
    def save(self) -> None:
        """Save current configuration to file."""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        with open(self.config_path, 'w') as f:
            yaml.dump(self._config, f, default_flow_style=False)
    
    def init_config(self) -> None:
        """Initialize a new configuration file with prompts."""
        from prompt_toolkit import prompt
        from prompt_toolkit.validation import Validator
        
        print("🚀 Initializing Notion CLI configuration")
        print("-" * 40)
        
        # API Key
        api_key = prompt(
            "Enter your Notion API key: ",
            is_password=True,
            validator=Validator.from_callable(
                lambda x: len(x) > 0,
                error_message="API key cannot be empty"
            )
        )
        
        # Default database (optional)
        default_db = prompt(
            "Enter default database ID (optional, press Enter to skip): "
        )
        
        # Output format
        output_format = prompt(
            "Default output format [json/yaml/table/text] (default: json): "
        ) or "json"
        
        # Color output
        color_output = prompt(
            "Enable colored output? [Y/n] (default: Y): "
        )
        color_output = color_output.lower() != 'n'
        
        # Update config
        self._config.update({
            "api_key": api_key,
            "output_format": output_format,
            "color_output": color_output
        })
        
        if default_db:
            self._config["default_database"] = default_db
        
        # Save config
        self.save()
        
        print(f"\n✅ Configuration saved to: {self.config_path}")
        print("\nYou can now use notion-cli!")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value.
        
        Args:
            key: Configuration key
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        return self._config.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set a configuration value.
        
        Args:
            key: Configuration key
            value: Configuration value
        """
        self._config[key] = value
    
    @property
    def api_key(self) -> Optional[str]:
        """Get API key."""
        return self.get("api_key")
    
    @property
    def default_database(self) -> Optional[str]:
        """Get default database ID."""
        return self.get("default_database")
    
    @property
    def output_format(self) -> str:
        """Get output format."""
        return self.get("output_format", "json")
    
    @property
    def color_output(self) -> bool:
        """Get color output setting."""
        return self.get("color_output", True)
    
    @property
    def page_size(self) -> int:
        """Get page size for API requests."""
        return self.get("page_size", 100)
    
    def __repr__(self) -> str:
        """String representation."""
        return f"Config(path={self.config_path}, keys={list(self._config.keys())})"