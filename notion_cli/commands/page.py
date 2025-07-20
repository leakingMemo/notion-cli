"""Page-related commands."""

import click
import json
from typing import Optional, Dict, Any
from pathlib import Path

from ..client import NotionClient
from ..cli import print_output, handle_error


@click.group()
def page():
    """Manage Notion pages."""
    pass


@page.command()
@click.argument("page_id")
@click.option("--output", "-o", default=None, help="Output format")
@click.pass_context
def get(ctx: click.Context, page_id: str, output: Optional[str]):
    """Get a page by ID."""
    config = ctx.obj["config"]
    debug = ctx.obj.get("debug", False)
    output_format = output or config.output_format
    
    try:
        client = NotionClient(config.api_key)
        page_data = client.get_page(page_id)
        print_output(page_data, output_format, config.color_output)
    except Exception as e:
        handle_error(e, debug)


@page.command()
@click.option("--title", "-t", required=True, help="Page title")
@click.option("--parent", "-p", required=True, help="Parent page/database ID")
@click.option("--property", "properties", multiple=True, help="Property: name=value")
@click.option("--content", "-c", help="Page content (text or file path)")
@click.option("--icon", help="Page icon (emoji or URL)")
@click.option("--cover", help="Page cover image URL")
@click.option("--output", "-o", default=None, help="Output format")
@click.pass_context
def create(ctx: click.Context, title: str, parent: str, properties: tuple, 
           content: Optional[str], icon: Optional[str], cover: Optional[str],
           output: Optional[str]):
    """Create a new page."""
    config = ctx.obj["config"]
    debug = ctx.obj.get("debug", False)
    output_format = output or config.output_format
    
    try:
        client = NotionClient(config.api_key)
        
        # Build properties
        page_properties = {
            "title": {
                "title": [{
                    "type": "text",
                    "text": {"content": title}
                }]
            }
        }
        
        # Parse additional properties
        for prop in properties:
            if "=" not in prop:
                click.echo(f"Error: Invalid property format: {prop}")
                ctx.exit(1)
            name, value = prop.split("=", 1)
            
            # Try to infer property type
            if value.lower() in ["true", "false"]:
                page_properties[name] = {"checkbox": value.lower() == "true"}
            elif value.isdigit():
                page_properties[name] = {"number": int(value)}
            else:
                # Default to rich text
                page_properties[name] = {
                    "rich_text": [{
                        "type": "text",
                        "text": {"content": value}
                    }]
                }
        
        # Build children blocks if content provided
        children = []
        if content:
            # Check if content is a file path
            content_path = Path(content)
            if content_path.exists() and content_path.is_file():
                content_text = content_path.read_text()
            else:
                content_text = content
            
            # Split content into paragraphs
            for paragraph in content_text.split("\n\n"):
                if paragraph.strip():
                    children.append({
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [{
                                "type": "text",
                                "text": {"content": paragraph.strip()}
                            }]
                        }
                    })
        
        # Handle icon
        icon_obj = None
        if icon:
            if len(icon) <= 2:  # Likely an emoji
                icon_obj = {"type": "emoji", "emoji": icon}
            else:  # URL
                icon_obj = {"type": "external", "external": {"url": icon}}
        
        # Handle cover
        cover_obj = None
        if cover:
            cover_obj = {"type": "external", "external": {"url": cover}}
        
        # Create page
        page_data = client.create_page(
            parent=parent,
            properties=page_properties,
            children=children if children else None,
            icon=icon_obj,
            cover=cover_obj
        )
        
        print_output(page_data, output_format, config.color_output)
        
    except Exception as e:
        handle_error(e, debug)


@page.command()
@click.argument("page_id")
@click.option("--title", "-t", help="New page title")
@click.option("--property", "properties", multiple=True, help="Property: name=value")
@click.option("--archived", is_flag=True, help="Archive the page")
@click.option("--icon", help="Page icon (emoji or URL)")
@click.option("--cover", help="Page cover image URL")
@click.option("--output", "-o", default=None, help="Output format")
@click.pass_context
def update(ctx: click.Context, page_id: str, title: Optional[str],
           properties: tuple, archived: bool, icon: Optional[str],
           cover: Optional[str], output: Optional[str]):
    """Update a page."""
    config = ctx.obj["config"]
    debug = ctx.obj.get("debug", False)
    output_format = output or config.output_format
    
    try:
        client = NotionClient(config.api_key)
        
        # Build properties to update
        page_properties = {}
        
        if title:
            page_properties["title"] = {
                "title": [{
                    "type": "text",
                    "text": {"content": title}
                }]
            }
        
        # Parse additional properties
        for prop in properties:
            if "=" not in prop:
                click.echo(f"Error: Invalid property format: {prop}")
                ctx.exit(1)
            name, value = prop.split("=", 1)
            
            # Try to infer property type
            if value.lower() in ["true", "false"]:
                page_properties[name] = {"checkbox": value.lower() == "true"}
            elif value.isdigit():
                page_properties[name] = {"number": int(value)}
            else:
                # Default to rich text
                page_properties[name] = {
                    "rich_text": [{
                        "type": "text",
                        "text": {"content": value}
                    }]
                }
        
        # Handle icon
        icon_obj = None
        if icon:
            if icon == "none":
                icon_obj = None
            elif len(icon) <= 2:  # Likely an emoji
                icon_obj = {"type": "emoji", "emoji": icon}
            else:  # URL
                icon_obj = {"type": "external", "external": {"url": icon}}
        
        # Handle cover
        cover_obj = None
        if cover:
            if cover == "none":
                cover_obj = None
            else:
                cover_obj = {"type": "external", "external": {"url": cover}}
        
        # Update page
        update_params = {}
        if page_properties:
            update_params["properties"] = page_properties
        if archived:
            update_params["archived"] = True
        if icon is not None:
            update_params["icon"] = icon_obj
        if cover is not None:
            update_params["cover"] = cover_obj
        
        if not update_params:
            click.echo("Error: No updates specified")
            ctx.exit(1)
        
        page_data = client.update_page(page_id, **update_params)
        print_output(page_data, output_format, config.color_output)
        
    except Exception as e:
        handle_error(e, debug)


@page.command()
@click.argument("page_id")
@click.option("--confirm", is_flag=True, help="Skip confirmation")
@click.pass_context
def delete(ctx: click.Context, page_id: str, confirm: bool):
    """Delete (archive) a page."""
    config = ctx.obj["config"]
    debug = ctx.obj.get("debug", False)
    
    try:
        if not confirm:
            click.confirm("Are you sure you want to archive this page?", abort=True)
        
        client = NotionClient(config.api_key)
        client.delete_page(page_id)
        click.echo(f"✅ Page {page_id} archived successfully")
        
    except Exception as e:
        handle_error(e, debug)


@page.command()
@click.argument("query")
@click.option("--limit", "-l", default=10, help="Maximum results")
@click.option("--output", "-o", default=None, help="Output format")
@click.pass_context
def search(ctx: click.Context, query: str, limit: int, output: Optional[str]):
    """Search for pages."""
    config = ctx.obj["config"]
    debug = ctx.obj.get("debug", False)
    output_format = output or config.output_format
    
    try:
        client = NotionClient(config.api_key)
        results = client.search(query=query, filter_type="page", page_size=limit)
        print_output(results, output_format, config.color_output)
        
    except Exception as e:
        handle_error(e, debug)


@page.command()
@click.argument("page_id")
@click.option("--format", "-f", "export_format", default="markdown",
              type=click.Choice(["markdown", "html", "text"]),
              help="Export format")
@click.option("--output-file", "-o", type=click.Path(), help="Output file path")
@click.option("--include-children", is_flag=True, help="Include child blocks")
@click.pass_context
def export(ctx: click.Context, page_id: str, export_format: str,
           output_file: Optional[str], include_children: bool):
    """Export a page to various formats."""
    config = ctx.obj["config"]
    debug = ctx.obj.get("debug", False)
    
    try:
        client = NotionClient(config.api_key)
        
        # Get page data
        page_data = client.get_page(page_id)
        
        # Get blocks if requested
        blocks = []
        if include_children:
            blocks = client.get_block_children(page_id)
        
        # Export based on format
        if export_format == "markdown":
            content = export_to_markdown(page_data, blocks)
        elif export_format == "html":
            content = export_to_html(page_data, blocks)
        else:  # text
            content = export_to_text(page_data, blocks)
        
        # Output
        if output_file:
            Path(output_file).write_text(content)
            click.echo(f"✅ Exported to {output_file}")
        else:
            click.echo(content)
        
    except Exception as e:
        handle_error(e, debug)


def export_to_markdown(page: Dict[str, Any], blocks: list) -> str:
    """Export page to Markdown format."""
    lines = []
    
    # Extract title
    title = "Untitled"
    for prop in page.get("properties", {}).values():
        if prop.get("type") == "title":
            title_arr = prop.get("title", [])
            if title_arr:
                title = title_arr[0].get("plain_text", "Untitled")
            break
    
    lines.append(f"# {title}\n")
    
    # Add metadata
    lines.append(f"*Created: {page.get('created_time', 'Unknown')}*")
    lines.append(f"*Last edited: {page.get('last_edited_time', 'Unknown')}*")
    lines.append(f"*URL: {page.get('url', 'Unknown')}*\n")
    
    # Process blocks
    for block in blocks:
        block_type = block.get("type")
        block_data = block.get(block_type, {})
        
        if block_type == "paragraph":
            text = extract_text_from_rich_text(block_data.get("rich_text", []))
            lines.append(f"{text}\n")
        elif block_type.startswith("heading_"):
            level = int(block_type[-1])
            text = extract_text_from_rich_text(block_data.get("rich_text", []))
            lines.append(f"{'#' * level} {text}\n")
        elif block_type == "bulleted_list_item":
            text = extract_text_from_rich_text(block_data.get("rich_text", []))
            lines.append(f"- {text}")
        elif block_type == "numbered_list_item":
            text = extract_text_from_rich_text(block_data.get("rich_text", []))
            lines.append(f"1. {text}")
        elif block_type == "to_do":
            text = extract_text_from_rich_text(block_data.get("rich_text", []))
            checked = "x" if block_data.get("checked", False) else " "
            lines.append(f"- [{checked}] {text}")
        elif block_type == "code":
            language = block_data.get("language", "")
            code = extract_text_from_rich_text(block_data.get("rich_text", []))
            lines.append(f"```{language}\n{code}\n```\n")
        elif block_type == "quote":
            text = extract_text_from_rich_text(block_data.get("rich_text", []))
            lines.append(f"> {text}\n")
        elif block_type == "divider":
            lines.append("---\n")
        else:
            lines.append(f"[{block_type} block]\n")
    
    return "\n".join(lines)


def export_to_html(page: Dict[str, Any], blocks: list) -> str:
    """Export page to HTML format."""
    # Simplified HTML export
    lines = ["<!DOCTYPE html>", "<html>", "<head>", "<title>Page Export</title>", "</head>", "<body>"]
    
    # Extract title
    title = "Untitled"
    for prop in page.get("properties", {}).values():
        if prop.get("type") == "title":
            title_arr = prop.get("title", [])
            if title_arr:
                title = title_arr[0].get("plain_text", "Untitled")
            break
    
    lines.append(f"<h1>{title}</h1>")
    
    # Process blocks
    for block in blocks:
        block_type = block.get("type")
        block_data = block.get(block_type, {})
        
        if block_type == "paragraph":
            text = extract_text_from_rich_text(block_data.get("rich_text", []))
            lines.append(f"<p>{text}</p>")
        elif block_type.startswith("heading_"):
            level = int(block_type[-1])
            text = extract_text_from_rich_text(block_data.get("rich_text", []))
            lines.append(f"<h{level}>{text}</h{level}>")
        # ... add more block types as needed
    
    lines.extend(["</body>", "</html>"])
    return "\n".join(lines)


def export_to_text(page: Dict[str, Any], blocks: list) -> str:
    """Export page to plain text format."""
    lines = []
    
    # Extract title
    title = "Untitled"
    for prop in page.get("properties", {}).values():
        if prop.get("type") == "title":
            title_arr = prop.get("title", [])
            if title_arr:
                title = title_arr[0].get("plain_text", "Untitled")
            break
    
    lines.append(title)
    lines.append("=" * len(title))
    lines.append("")
    
    # Process blocks
    for block in blocks:
        block_type = block.get("type")
        block_data = block.get(block_type, {})
        
        if "rich_text" in block_data:
            text = extract_text_from_rich_text(block_data.get("rich_text", []))
            lines.append(text)
            lines.append("")
    
    return "\n".join(lines)


def extract_text_from_rich_text(rich_text: list) -> str:
    """Extract plain text from rich text array."""
    return "".join([t.get("plain_text", "") for t in rich_text])