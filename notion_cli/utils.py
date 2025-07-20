"""Utility functions for Notion CLI."""

import sys
from typing import Any
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from .formatters import get_formatter, NotionDataFormatter

console = Console()


def print_output(data: Any, format_type: str, color: bool = True) -> None:
    """Print data in the specified format."""
    formatter = get_formatter(format_type, color)
    notion_formatter = NotionDataFormatter(formatter)
    
    # Determine the type of data and format appropriately
    if isinstance(data, dict):
        if data.get("object") == "page":
            output = notion_formatter.format_page(data)
        elif data.get("object") == "database":
            output = notion_formatter.format_database(data)
        elif data.get("object") == "list":
            # Handle paginated results
            results = data.get("results", [])
            if results and results[0].get("object") == "block":
                output = notion_formatter.format_blocks(results)
            else:
                output = notion_formatter.format_search_results(results)
        else:
            output = formatter.format(data)
    elif isinstance(data, list):
        # Check if it's a list of search results
        if data and isinstance(data[0], dict) and "object" in data[0]:
            output = notion_formatter.format_search_results(data)
        else:
            output = formatter.format(data)
    else:
        output = formatter.format(data)
    
    if hasattr(output, "__rich__"):
        console.print(output)
    else:
        print(output)


def handle_error(e: Exception, debug: bool = False) -> None:
    """Handle and display errors."""
    if debug:
        console.print_exception()
    else:
        error_panel = Panel(
            Text(str(e), style="red"),
            title="Error",
            border_style="red"
        )
        console.print(error_panel)
    sys.exit(1)