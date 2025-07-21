"""Main CLI interface for Notion CLI."""

import click
import sys
from typing import Optional, List, Dict, Any
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from .client import NotionClient
from .config import Config
from .utils import print_output, handle_error
from .commands import page, database, block, search, config as config_cmd, bulk
from .interactive import interactive_mode
from . import __version__

console = Console()


@click.group(invoke_without_command=True)
@click.option("--version", "-v", is_flag=True, help="Show version")
@click.option("--config", "-c", type=click.Path(), help="Path to config file")
@click.option("--debug", is_flag=True, help="Enable debug mode")
@click.pass_context
def cli(ctx: click.Context, version: bool, config: Optional[str], debug: bool):
    """Notion CLI - A powerful command-line interface for Notion.
    
    Manage pages, databases, and content directly from your terminal.
    
    Examples:
    
    \b
    # Search for pages
    notion-cli search "meeting notes"
    
    \b
    # Query a database
    notion-cli database query <database-id> --filter "Status=Done"
    
    \b
    # Create a new page
    notion-cli page create --title "My Page" --parent <parent-id>
    
    \b
    # Start interactive mode
    notion-cli interactive
    """
    if version:
        click.echo(f"Notion CLI version {__version__}")
        ctx.exit()
    
    # Store debug flag in context
    ctx.ensure_object(dict)
    ctx.obj["debug"] = debug
    
    # Initialize config
    config_path = None
    if config:
        from pathlib import Path
        config_path = Path(config)
    
    ctx.obj["config"] = Config(config_path)
    
    # If no command is provided, show help
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


# Add command groups
cli.add_command(page.page)
cli.add_command(database.database)
cli.add_command(block.block)
cli.add_command(search.search_cmd)
cli.add_command(config_cmd.config)
cli.add_command(bulk.bulk)
cli.add_command(interactive_mode)


def main():
    """Main entry point."""
    try:
        cli(obj={})
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main()