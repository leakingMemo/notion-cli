"""Configuration management commands."""

import click
from typing import Optional
from pathlib import Path

from ..config import Config
from ..utils import print_output


@click.group()
def config():
    """Manage notion-cli configuration."""
    pass


@config.command()
@click.pass_context
def init(ctx: click.Context):
    """Initialize configuration with interactive setup."""
    config_obj = ctx.obj["config"]
    config_obj.init_config()


@config.command()
@click.option("--output", "-o", default="yaml", help="Output format")
@click.pass_context
def show(ctx: click.Context, output: str):
    """Show current configuration."""
    config_obj = ctx.obj["config"]
    
    # Get config as dict
    config_data = dict(config_obj._config)
    
    # Mask API key for security
    if "api_key" in config_data:
        api_key = config_data["api_key"]
        if api_key and len(api_key) > 10:
            config_data["api_key"] = f"{api_key[:10]}...{api_key[-4:]}"
    
    # Add meta information
    config_data["_config_path"] = str(config_obj.config_path)
    config_data["_config_exists"] = config_obj.config_path.exists()
    
    print_output(config_data, output, config_obj.color_output)


@config.command()
@click.argument("key")
@click.argument("value")
@click.pass_context
def set(ctx: click.Context, key: str, value: str):
    """Set a configuration value."""
    config_obj = ctx.obj["config"]
    
    # Handle boolean values
    if key in ["color_output"]:
        value = value.lower() in ["true", "1", "yes"]
    # Handle integer values
    elif key in ["page_size"]:
        try:
            value = int(value)
        except ValueError:
            click.echo(f"Error: {key} must be a number")
            ctx.exit(1)
    
    config_obj.set(key, value)
    config_obj.save()
    
    click.echo(f"✅ Set {key} = {value}")


@config.command()
@click.argument("key")
@click.pass_context
def get(ctx: click.Context, key: str):
    """Get a configuration value."""
    config_obj = ctx.obj["config"]
    value = config_obj.get(key)
    
    if value is None:
        click.echo(f"Configuration key '{key}' not found")
        ctx.exit(1)
    
    # Mask API key for security
    if key == "api_key" and value and len(value) > 10:
        value = f"{value[:10]}...{value[-4:]}"
    
    click.echo(value)


@config.command()
@click.argument("key")
@click.option("--confirm", is_flag=True, help="Skip confirmation")
@click.pass_context
def unset(ctx: click.Context, key: str, confirm: bool):
    """Remove a configuration value."""
    config_obj = ctx.obj["config"]
    
    if key not in config_obj._config:
        click.echo(f"Configuration key '{key}' not found")
        ctx.exit(1)
    
    if not confirm:
        click.confirm(f"Remove configuration key '{key}'?", abort=True)
    
    del config_obj._config[key]
    config_obj.save()
    
    click.echo(f"✅ Removed {key}")


@config.command()
@click.pass_context
def path(ctx: click.Context):
    """Show configuration file path."""
    config_obj = ctx.obj["config"]
    click.echo(str(config_obj.config_path))


@config.command()
@click.option("--editor", "-e", help="Editor to use")
@click.pass_context
def edit(ctx: click.Context, editor: Optional[str]):
    """Open configuration file in editor."""
    config_obj = ctx.obj["config"]
    
    if not config_obj.config_path.exists():
        click.echo("Configuration file does not exist. Run 'notion-cli config init' first.")
        ctx.exit(1)
    
    # Determine editor
    import os
    editor = editor or os.environ.get("EDITOR", "nano")
    
    # Open in editor
    click.edit(filename=str(config_obj.config_path), editor=editor)