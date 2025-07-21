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
from .commands import page, database, block, search, config as config_cmd, user
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
cli.add_command(user.user)
cli.add_command(interactive_mode)


@cli.command()
@click.option("--filter", "-f", "filters", multiple=True, help="Filter: property=value")
@click.option("--set", "-s", "updates", multiple=True, help="Update: property=value")
@click.option("--output", "-o", default=None, help="Output format")
@click.option("--dry-run", is_flag=True, help="Show what would be updated")
@click.pass_context
def bulk(ctx: click.Context, filters: List[str], updates: List[str], output: Optional[str], dry_run: bool):
    """Perform bulk operations on pages."""
    config = ctx.obj["config"]
    debug = ctx.obj.get("debug", False)
    
    if not updates:
        click.echo("Error: No updates specified. Use --set property=value")
        ctx.exit(1)
    
    try:
        # Initialize client
        client = NotionClient(config.api_key)
        
        # Parse filters
        filter_dict = {}
        for f in filters:
            if "=" not in f:
                click.echo(f"Error: Invalid filter format: {f}")
                ctx.exit(1)
            key, value = f.split("=", 1)
            filter_dict[key] = value
        
        # Parse updates
        update_dict = {}
        for u in updates:
            if "=" not in u:
                click.echo(f"Error: Invalid update format: {u}")
                ctx.exit(1)
            key, value = u.split("=", 1)
            update_dict[key] = value
        
        # Search for pages matching filters
        # This is a simplified implementation - in reality, you'd need to
        # construct proper Notion filters
        pages = client.search(filter_type="page")
        
        # Filter pages (simplified)
        matching_pages = []
        for page in pages:
            # Check if page matches all filters
            matches = True
            for key, expected_value in filter_dict.items():
                # This is simplified - real implementation would need to
                # properly check property values
                props = page.get("properties", {})
                if key not in props:
                    matches = False
                    break
            
            if matches:
                matching_pages.append(page)
        
        if dry_run:
            click.echo(f"Would update {len(matching_pages)} pages:")
            for page in matching_pages[:5]:  # Show first 5
                title = "Untitled"
                for prop in page.get("properties", {}).values():
                    if prop.get("type") == "title":
                        title_arr = prop.get("title", [])
                        if title_arr:
                            title = title_arr[0].get("plain_text", "Untitled")
                        break
                click.echo(f"  - {title} ({page['id']})")
            
            if len(matching_pages) > 5:
                click.echo(f"  ... and {len(matching_pages) - 5} more")
            
            click.echo(f"\nUpdates to apply: {update_dict}")
        else:
            # Perform updates
            updated_count = 0
            for page in matching_pages:
                try:
                    # Construct property updates
                    # This is simplified - real implementation would need to
                    # properly format property values based on their types
                    properties = {}
                    for key, value in update_dict.items():
                        # Simplified - assumes text properties
                        properties[key] = {
                            "rich_text": [{
                                "type": "text",
                                "text": {"content": value}
                            }]
                        }
                    
                    client.update_page(page["id"], properties=properties)
                    updated_count += 1
                except Exception as e:
                    click.echo(f"Failed to update page {page['id']}: {e}")
            
            click.echo(f"Successfully updated {updated_count} pages")
        
    except Exception as e:
        handle_error(e, debug)


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