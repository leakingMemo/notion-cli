"""Search command."""

import click
from typing import Optional

from ..client import NotionClient
from ..utils import print_output, handle_error


@click.command(name="search")
@click.argument("query", default="")
@click.option("--type", "-t", "filter_type",
              type=click.Choice(["page", "database", "all"]),
              default="all", help="Filter by type")
@click.option("--limit", "-l", default=20, help="Maximum results")
@click.option("--sort", "-s", type=click.Choice(["relevance", "last_edited"]),
              default="relevance", help="Sort order")
@click.option("--output", "-o", default=None, help="Output format")
@click.pass_context
def search_cmd(ctx: click.Context, query: str, filter_type: str,
               limit: int, sort: str, output: Optional[str]):
    """Search across your Notion workspace.
    
    Examples:
    
    \b
    # Search for pages containing "meeting"
    notion-cli search meeting
    
    \b
    # Search only databases
    notion-cli search "project tracker" --type database
    
    \b
    # Get recently edited items
    notion-cli search --sort last_edited --limit 10
    """
    config = ctx.obj["config"]
    debug = ctx.obj.get("debug", False)
    output_format = output or config.output_format
    
    try:
        client = NotionClient(config.api_key)
        
        # Build sort parameter
        sort_param = None
        if sort == "last_edited":
            sort_param = {
                "direction": "descending",
                "timestamp": "last_edited_time"
            }
        
        # Perform search
        if filter_type == "all":
            results = client.search(
                query=query,
                sort=sort_param,
                page_size=limit
            )
        else:
            results = client.search(
                query=query,
                filter_type=filter_type,
                sort=sort_param,
                page_size=limit
            )
        
        # Limit results
        if len(results) > limit:
            results = results[:limit]
        
        # Output results
        if not results:
            if query:
                click.echo(f"No results found for: {query}")
            else:
                click.echo("No accessible content found")
        else:
            print_output(results, output_format, config.color_output)
        
    except Exception as e:
        handle_error(e, debug)