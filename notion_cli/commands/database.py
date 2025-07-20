"""Database-related commands."""

import click
import json
import csv
from typing import Optional, List, Dict, Any
from pathlib import Path
from io import StringIO

from ..client import NotionClient
from ..cli import print_output, handle_error


@click.group()
def database():
    """Manage Notion databases."""
    pass


@database.command()
@click.option("--output", "-o", default=None, help="Output format")
@click.pass_context
def list(ctx: click.Context, output: Optional[str]):
    """List all accessible databases."""
    config = ctx.obj["config"]
    debug = ctx.obj.get("debug", False)
    output_format = output or config.output_format
    
    try:
        client = NotionClient(config.api_key)
        databases = client.list_databases()
        print_output(databases, output_format, config.color_output)
    except Exception as e:
        handle_error(e, debug)


@database.command()
@click.argument("database_id")
@click.option("--output", "-o", default=None, help="Output format")
@click.pass_context
def get(ctx: click.Context, database_id: str, output: Optional[str]):
    """Get database metadata."""
    config = ctx.obj["config"]
    debug = ctx.obj.get("debug", False)
    output_format = output or config.output_format
    
    try:
        client = NotionClient(config.api_key)
        db_data = client.get_database(database_id)
        print_output(db_data, output_format, config.color_output)
    except Exception as e:
        handle_error(e, debug)


@database.command()
@click.argument("database_id")
@click.option("--filter", "-f", "filters", multiple=True, help="Filter: property=value")
@click.option("--sort", "-s", "sorts", multiple=True, help="Sort: property:direction")
@click.option("--limit", "-l", type=int, help="Maximum results")
@click.option("--output", "-o", default=None, help="Output format")
@click.pass_context
def query(ctx: click.Context, database_id: str, filters: tuple, sorts: tuple,
          limit: Optional[int], output: Optional[str]):
    """Query a database with filters and sorts.
    
    Examples:
    
    \b
    # Filter by status
    notion-cli database query <id> --filter "Status=Done"
    
    \b
    # Multiple filters
    notion-cli database query <id> -f "Status=In Progress" -f "Priority=High"
    
    \b
    # Sort by date
    notion-cli database query <id> --sort "Due Date:ascending"
    """
    config = ctx.obj["config"]
    debug = ctx.obj.get("debug", False)
    output_format = output or config.output_format
    
    try:
        client = NotionClient(config.api_key)
        
        # Parse filters
        filter_obj = None
        if filters:
            filter_conditions = []
            for f in filters:
                if "=" not in f:
                    click.echo(f"Error: Invalid filter format: {f}")
                    ctx.exit(1)
                prop, value = f.split("=", 1)
                
                # Simple filter construction - in reality this would need
                # to handle different property types
                if value.lower() in ["true", "false"]:
                    filter_conditions.append({
                        "property": prop,
                        "checkbox": {"equals": value.lower() == "true"}
                    })
                elif value in ["empty", "not_empty"]:
                    filter_conditions.append({
                        "property": prop,
                        prop.lower(): {f"is_{value}": True}
                    })
                else:
                    # Assume select/text for now
                    filter_conditions.append({
                        "property": prop,
                        "select": {"equals": value}
                    })
            
            if len(filter_conditions) == 1:
                filter_obj = filter_conditions[0]
            else:
                filter_obj = {"and": filter_conditions}
        
        # Parse sorts
        sort_list = []
        if sorts:
            for s in sorts:
                if ":" not in s:
                    click.echo(f"Error: Invalid sort format: {s}")
                    ctx.exit(1)
                prop, direction = s.split(":", 1)
                if direction not in ["ascending", "descending"]:
                    click.echo(f"Error: Invalid sort direction: {direction}")
                    ctx.exit(1)
                sort_list.append({
                    "property": prop,
                    "direction": direction
                })
        
        # Query database
        page_size = min(limit, 100) if limit else 100
        results = client.query_database(
            database_id,
            filter=filter_obj,
            sorts=sort_list if sort_list else None,
            page_size=page_size
        )
        
        # Apply limit if specified
        if limit and len(results) > limit:
            results = results[:limit]
        
        print_output(results, output_format, config.color_output)
        
    except Exception as e:
        handle_error(e, debug)


@database.command(name="create-page")
@click.argument("database_id")
@click.option("--property", "-p", "properties", multiple=True, required=True,
              help="Property: name=value")
@click.option("--output", "-o", default=None, help="Output format")
@click.pass_context
def create_page(ctx: click.Context, database_id: str, properties: tuple,
                output: Optional[str]):
    """Create a new page in a database.
    
    Examples:
    
    \b
    # Create a task
    notion-cli database create-page <id> \\
        --property "Name=New Task" \\
        --property "Status=To Do" \\
        --property "Priority=High"
    """
    config = ctx.obj["config"]
    debug = ctx.obj.get("debug", False)
    output_format = output or config.output_format
    
    try:
        client = NotionClient(config.api_key)
        
        # First, get the database schema to understand property types
        db_schema = client.get_database(database_id)
        db_properties = db_schema.get("properties", {})
        
        # Build properties
        page_properties = {}
        for prop in properties:
            if "=" not in prop:
                click.echo(f"Error: Invalid property format: {prop}")
                ctx.exit(1)
            name, value = prop.split("=", 1)
            
            # Check if property exists in schema
            if name not in db_properties:
                click.echo(f"Warning: Property '{name}' not found in database schema")
                continue
            
            prop_type = db_properties[name].get("type")
            
            # Format value based on property type
            if prop_type == "title":
                page_properties[name] = {
                    "title": [{
                        "type": "text",
                        "text": {"content": value}
                    }]
                }
            elif prop_type == "rich_text":
                page_properties[name] = {
                    "rich_text": [{
                        "type": "text",
                        "text": {"content": value}
                    }]
                }
            elif prop_type == "number":
                try:
                    page_properties[name] = {"number": float(value)}
                except ValueError:
                    click.echo(f"Error: Invalid number value for {name}: {value}")
                    ctx.exit(1)
            elif prop_type == "checkbox":
                page_properties[name] = {"checkbox": value.lower() in ["true", "1", "yes"]}
            elif prop_type == "select":
                page_properties[name] = {"select": {"name": value}}
            elif prop_type == "multi_select":
                # Support comma-separated values
                values = [v.strip() for v in value.split(",")]
                page_properties[name] = {
                    "multi_select": [{"name": v} for v in values]
                }
            elif prop_type == "date":
                page_properties[name] = {"date": {"start": value}}
            elif prop_type == "url":
                page_properties[name] = {"url": value}
            elif prop_type == "email":
                page_properties[name] = {"email": value}
            elif prop_type == "phone_number":
                page_properties[name] = {"phone_number": value}
            else:
                click.echo(f"Warning: Unsupported property type '{prop_type}' for '{name}'")
        
        # Create the page
        page_data = client.create_page(
            parent=database_id,
            properties=page_properties
        )
        
        print_output(page_data, output_format, config.color_output)
        
    except Exception as e:
        handle_error(e, debug)


@database.command()
@click.argument("database_id")
@click.option("--format", "-f", "export_format", default="csv",
              type=click.Choice(["csv", "json", "excel"]),
              help="Export format")
@click.option("--output-file", "-o", type=click.Path(), help="Output file path")
@click.option("--filter", "filters", multiple=True, help="Filter: property=value")
@click.pass_context
def export(ctx: click.Context, database_id: str, export_format: str,
           output_file: Optional[str], filters: tuple):
    """Export database to CSV, JSON, or Excel."""
    config = ctx.obj["config"]
    debug = ctx.obj.get("debug", False)
    
    try:
        client = NotionClient(config.api_key)
        
        # Get database schema first
        db_schema = client.get_database(database_id)
        db_properties = db_schema.get("properties", {})
        
        # Parse filters (simplified)
        filter_obj = None
        if filters:
            filter_conditions = []
            for f in filters:
                if "=" not in f:
                    click.echo(f"Error: Invalid filter format: {f}")
                    ctx.exit(1)
                prop, value = f.split("=", 1)
                filter_conditions.append({
                    "property": prop,
                    "select": {"equals": value}
                })
            
            if len(filter_conditions) == 1:
                filter_obj = filter_conditions[0]
            else:
                filter_obj = {"and": filter_conditions}
        
        # Query all pages
        pages = client.query_database(database_id, filter=filter_obj)
        
        # Export based on format
        if export_format == "csv":
            content = export_to_csv(pages, db_properties)
        elif export_format == "json":
            content = json.dumps(pages, indent=2, default=str)
        else:  # excel
            click.echo("Excel export not yet implemented")
            ctx.exit(1)
        
        # Output
        if output_file:
            Path(output_file).write_text(content)
            click.echo(f"✅ Exported {len(pages)} records to {output_file}")
        else:
            click.echo(content)
        
    except Exception as e:
        handle_error(e, debug)


@database.command()
@click.option("--parent", "-p", required=True, help="Parent page ID")
@click.option("--title", "-t", required=True, help="Database title")
@click.option("--schema", "-s", type=click.Path(exists=True),
              help="Schema definition file (JSON)")
@click.option("--output", "-o", default=None, help="Output format")
@click.pass_context
def create(ctx: click.Context, parent: str, title: str, schema: Optional[str],
           output: Optional[str]):
    """Create a new database."""
    config = ctx.obj["config"]
    debug = ctx.obj.get("debug", False)
    output_format = output or config.output_format
    
    try:
        client = NotionClient(config.api_key)
        
        # Load schema if provided
        properties = {}
        if schema:
            with open(schema, 'r') as f:
                schema_data = json.load(f)
                properties = schema_data.get("properties", {})
        else:
            # Default schema with just a title
            properties = {
                "Name": {
                    "title": {}
                }
            }
        
        # Create database
        db_data = client.create_database(
            parent=parent,
            title=title,
            properties=properties
        )
        
        print_output(db_data, output_format, config.color_output)
        
    except Exception as e:
        handle_error(e, debug)


def export_to_csv(pages: List[Dict[str, Any]], schema: Dict[str, Any]) -> str:
    """Export pages to CSV format."""
    if not pages:
        return ""
    
    # Extract all property names from schema
    headers = list(schema.keys())
    headers.insert(0, "Page ID")
    headers.append("Created Time")
    headers.append("Last Edited Time")
    headers.append("URL")
    
    # Create CSV
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=headers, extrasaction='ignore')
    writer.writeheader()
    
    for page in pages:
        row = {
            "Page ID": page.get("id"),
            "Created Time": page.get("created_time"),
            "Last Edited Time": page.get("last_edited_time"),
            "URL": page.get("url")
        }
        
        # Extract properties
        props = page.get("properties", {})
        for name, prop_data in props.items():
            prop_type = prop_data.get("type")
            
            if prop_type == "title":
                title_arr = prop_data.get("title", [])
                row[name] = title_arr[0].get("plain_text", "") if title_arr else ""
            elif prop_type == "rich_text":
                text_arr = prop_data.get("rich_text", [])
                row[name] = text_arr[0].get("plain_text", "") if text_arr else ""
            elif prop_type == "number":
                row[name] = prop_data.get("number", "")
            elif prop_type == "checkbox":
                row[name] = prop_data.get("checkbox", False)
            elif prop_type == "select":
                select = prop_data.get("select")
                row[name] = select.get("name", "") if select else ""
            elif prop_type == "multi_select":
                items = prop_data.get("multi_select", [])
                row[name] = ", ".join([item.get("name", "") for item in items])
            elif prop_type == "date":
                date = prop_data.get("date")
                row[name] = date.get("start", "") if date else ""
            elif prop_type == "url":
                row[name] = prop_data.get("url", "")
            elif prop_type == "email":
                row[name] = prop_data.get("email", "")
            elif prop_type == "phone_number":
                row[name] = prop_data.get("phone_number", "")
            else:
                row[name] = str(prop_data)
        
        writer.writerow(row)
    
    return output.getvalue()