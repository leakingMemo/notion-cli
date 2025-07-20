"""Block-related commands."""

import click
from typing import Optional, List, Dict, Any

from ..client import NotionClient
from ..utils import print_output, handle_error


@click.group()
def block():
    """Manage Notion blocks."""
    pass


@block.command()
@click.argument("block_id")
@click.option("--limit", "-l", type=int, help="Maximum results")
@click.option("--output", "-o", default=None, help="Output format")
@click.pass_context
def children(ctx: click.Context, block_id: str, limit: Optional[int], output: Optional[str]):
    """Get children blocks of a page or block."""
    config = ctx.obj["config"]
    debug = ctx.obj.get("debug", False)
    output_format = output or config.output_format
    
    try:
        client = NotionClient(config.api_key)
        blocks = client.get_block_children(block_id)
        
        if limit:
            blocks = blocks[:limit]
        
        print_output(blocks, output_format, config.color_output)
        
    except Exception as e:
        handle_error(e, debug)


@block.command()
@click.argument("block_id")
@click.option("--text", "-t", help="Add paragraph text")
@click.option("--heading", "-h", help="Add heading (format: level:text, e.g., 1:Title)")
@click.option("--bullet", "-b", multiple=True, help="Add bullet list item")
@click.option("--number", "-n", multiple=True, help="Add numbered list item")
@click.option("--todo", multiple=True, help="Add todo item")
@click.option("--code", "-c", help="Add code block (format: language:code)")
@click.option("--quote", "-q", help="Add quote block")
@click.option("--divider", is_flag=True, help="Add divider")
@click.option("--output", "-o", default=None, help="Output format")
@click.pass_context
def append(ctx: click.Context, block_id: str, text: Optional[str],
           heading: Optional[str], bullet: tuple, number: tuple,
           todo: tuple, code: Optional[str], quote: Optional[str],
           divider: bool, output: Optional[str]):
    """Append blocks to a page or block.
    
    Examples:
    
    \b
    # Add a paragraph
    notion-cli block append <id> --text "This is a paragraph"
    
    \b
    # Add multiple blocks
    notion-cli block append <id> \\
        --heading "1:Section Title" \\
        --text "Some content" \\
        --bullet "First item" \\
        --bullet "Second item"
    """
    config = ctx.obj["config"]
    debug = ctx.obj.get("debug", False)
    output_format = output or config.output_format
    
    try:
        client = NotionClient(config.api_key)
        
        # Build children blocks
        children = []
        
        # Add text paragraph
        if text:
            children.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{
                        "type": "text",
                        "text": {"content": text}
                    }]
                }
            })
        
        # Add heading
        if heading:
            if ":" not in heading:
                click.echo("Error: Heading format should be level:text (e.g., 1:Title)")
                ctx.exit(1)
            level, heading_text = heading.split(":", 1)
            try:
                level_int = int(level)
                if level_int not in [1, 2, 3]:
                    click.echo("Error: Heading level must be 1, 2, or 3")
                    ctx.exit(1)
            except ValueError:
                click.echo("Error: Invalid heading level")
                ctx.exit(1)
            
            children.append({
                "object": "block",
                "type": f"heading_{level_int}",
                f"heading_{level_int}": {
                    "rich_text": [{
                        "type": "text",
                        "text": {"content": heading_text}
                    }]
                }
            })
        
        # Add bullet list items
        for item in bullet:
            children.append({
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [{
                        "type": "text",
                        "text": {"content": item}
                    }]
                }
            })
        
        # Add numbered list items
        for item in number:
            children.append({
                "object": "block",
                "type": "numbered_list_item",
                "numbered_list_item": {
                    "rich_text": [{
                        "type": "text",
                        "text": {"content": item}
                    }]
                }
            })
        
        # Add todo items
        for item in todo:
            # Check if item starts with [x] or [ ]
            checked = False
            todo_text = item
            if item.startswith("[x]") or item.startswith("[X]"):
                checked = True
                todo_text = item[3:].strip()
            elif item.startswith("[ ]"):
                todo_text = item[3:].strip()
            
            children.append({
                "object": "block",
                "type": "to_do",
                "to_do": {
                    "rich_text": [{
                        "type": "text",
                        "text": {"content": todo_text}
                    }],
                    "checked": checked
                }
            })
        
        # Add code block
        if code:
            if ":" in code:
                language, code_text = code.split(":", 1)
            else:
                language = "plain text"
                code_text = code
            
            children.append({
                "object": "block",
                "type": "code",
                "code": {
                    "rich_text": [{
                        "type": "text",
                        "text": {"content": code_text}
                    }],
                    "language": language
                }
            })
        
        # Add quote
        if quote:
            children.append({
                "object": "block",
                "type": "quote",
                "quote": {
                    "rich_text": [{
                        "type": "text",
                        "text": {"content": quote}
                    }]
                }
            })
        
        # Add divider
        if divider:
            children.append({
                "object": "block",
                "type": "divider",
                "divider": {}
            })
        
        if not children:
            click.echo("Error: No content specified")
            ctx.exit(1)
        
        # Append blocks
        result = client.append_blocks(block_id, children)
        print_output(result, output_format, config.color_output)
        
    except Exception as e:
        handle_error(e, debug)


@block.command()
@click.argument("block_id")
@click.option("--text", "-t", help="New text content")
@click.option("--checked", type=bool, help="For todo blocks: checked state")
@click.option("--output", "-o", default=None, help="Output format")
@click.pass_context
def update(ctx: click.Context, block_id: str, text: Optional[str],
           checked: Optional[bool], output: Optional[str]):
    """Update a block."""
    config = ctx.obj["config"]
    debug = ctx.obj.get("debug", False)
    output_format = output or config.output_format
    
    try:
        client = NotionClient(config.api_key)
        
        # Build update parameters
        update_params = {}
        
        # For now, we need to know the block type to update it properly
        # In a real implementation, we'd fetch the block first
        if text:
            # This is simplified - real implementation would need to know block type
            update_params["paragraph"] = {
                "rich_text": [{
                    "type": "text",
                    "text": {"content": text}
                }]
            }
        
        if checked is not None:
            update_params["to_do"] = {"checked": checked}
        
        if not update_params:
            click.echo("Error: No updates specified")
            ctx.exit(1)
        
        result = client.update_block(block_id, **update_params)
        print_output(result, output_format, config.color_output)
        
    except Exception as e:
        handle_error(e, debug)


@block.command()
@click.argument("block_id")
@click.option("--confirm", is_flag=True, help="Skip confirmation")
@click.pass_context
def delete(ctx: click.Context, block_id: str, confirm: bool):
    """Delete a block."""
    config = ctx.obj["config"]
    debug = ctx.obj.get("debug", False)
    
    try:
        if not confirm:
            click.confirm("Are you sure you want to delete this block?", abort=True)
        
        client = NotionClient(config.api_key)
        client.delete_block(block_id)
        click.echo(f"✅ Block {block_id} deleted successfully")
        
    except Exception as e:
        handle_error(e, debug)