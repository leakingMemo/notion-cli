"""Bulk operations for Notion CLI."""
import json
import csv
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.table import Table
from rich.prompt import Confirm

from ..client import NotionClient
from ..utils.formatting import format_output
from ..factories import PageFactory, PropertyFactory

console = Console()


@click.group()
@click.pass_context
def bulk(ctx):
    """Perform bulk operations on Notion pages and databases."""
    ctx.ensure_object(dict)
    ctx.obj['client'] = NotionClient()


def load_data_from_file(file_path: str, format: str) -> List[Dict[str, Any]]:
    """Load data from CSV or JSON file."""
    path = Path(file_path)
    if not path.exists():
        raise click.ClickException(f"File not found: {file_path}")
    
    data = []
    
    if format == 'csv':
        with open(path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            data = list(reader)
    elif format == 'json':
        with open(path, 'r', encoding='utf-8') as f:
            content = json.load(f)
            if isinstance(content, list):
                data = content
            elif isinstance(content, dict) and 'data' in content:
                data = content['data']
            else:
                raise click.ClickException("JSON must be an array or object with 'data' field")
    else:
        raise click.ClickException(f"Unsupported format: {format}")
    
    if not data:
        raise click.ClickException("No data found in file")
    
    return data


@bulk.command()
@click.argument('file_path', type=click.Path(exists=True))
@click.option('--parent-id', required=True, help='Parent page ID where pages will be created')
@click.option('--format', type=click.Choice(['csv', 'json']), default='csv', help='Input file format')
@click.option('--title-field', default='title', help='Field name for page title')
@click.option('--dry-run', is_flag=True, help='Preview operations without executing')
@click.option('--output', '-o', type=click.Choice(['json', 'table', 'yaml', 'text']), 
              default='table', help='Output format')
@click.pass_context
def create_pages(ctx, file_path: str, parent_id: str, format: str, title_field: str, 
                 dry_run: bool, output: str):
    """Create multiple pages from a CSV or JSON file.
    
    Example CSV format:
    title,content,status
    "Page 1","Content for page 1","Published"
    "Page 2","Content for page 2","Draft"
    
    Example JSON format:
    [
        {"title": "Page 1", "content": "Content for page 1", "status": "Published"},
        {"title": "Page 2", "content": "Content for page 2", "status": "Draft"}
    ]
    """
    client = ctx.obj['client']
    
    try:
        # Load data from file
        data = load_data_from_file(file_path, format)
        console.print(f"Loaded {len(data)} items from {file_path}")
        
        if dry_run:
            console.print("\n[yellow]DRY RUN MODE - No changes will be made[/yellow]\n")
            
            # Show preview table
            table = Table(title="Pages to be created")
            table.add_column("Title", style="cyan")
            table.add_column("Properties", style="green")
            
            for item in data[:10]:  # Show first 10 items
                title = item.get(title_field, "Untitled")
                props = {k: v for k, v in item.items() if k != title_field}
                table.add_row(title, str(props))
            
            if len(data) > 10:
                table.add_row("...", f"({len(data) - 10} more items)")
            
            console.print(table)
            return
        
        # Confirm operation
        if not Confirm.ask(f"Create {len(data)} pages?"):
            console.print("Operation cancelled")
            return
        
        # Create pages with progress bar
        created_pages = []
        failed_items = []
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=console
        ) as progress:
            task = progress.add_task("Creating pages...", total=len(data))
            
            for idx, item in enumerate(data):
                try:
                    # Get title
                    title = str(item.get(title_field, f"Page {idx + 1}"))
                    
                    # Build properties
                    properties = {}
                    for key, value in item.items():
                        if key != title_field and value:
                            # Simple text property for now
                            properties[key] = PropertyFactory.create_property('rich_text', value)
                    
                    # Create page
                    page = PageFactory.create_page(
                        parent_id=parent_id,
                        title=title,
                        properties=properties
                    )
                    
                    result = client.create_page(page)
                    created_pages.append({
                        'id': result['id'],
                        'title': title,
                        'url': result.get('url', '')
                    })
                    
                except Exception as e:
                    failed_items.append({
                        'item': item,
                        'error': str(e)
                    })
                
                progress.update(task, advance=1)
        
        # Show results
        console.print(f"\n✅ Successfully created {len(created_pages)} pages")
        
        if failed_items:
            console.print(f"❌ Failed to create {len(failed_items)} pages", style="red")
            for failed in failed_items[:5]:
                console.print(f"  - {failed['item'].get(title_field, 'Unknown')}: {failed['error']}")
            if len(failed_items) > 5:
                console.print(f"  ... and {len(failed_items) - 5} more")
        
        # Format output
        if output == 'json':
            click.echo(json.dumps({
                'created': created_pages,
                'failed': len(failed_items),
                'total': len(data)
            }, indent=2))
        elif output == 'table' and created_pages:
            table = Table(title="Created Pages")
            table.add_column("ID", style="cyan")
            table.add_column("Title", style="green")
            table.add_column("URL", style="blue")
            
            for page in created_pages[:20]:
                table.add_row(page['id'], page['title'], page['url'])
            
            if len(created_pages) > 20:
                table.add_row("...", f"({len(created_pages) - 20} more pages)", "...")
            
            console.print(table)
        
    except Exception as e:
        raise click.ClickException(str(e))


@bulk.command()
@click.argument('file_path', type=click.Path(exists=True))
@click.option('--format', type=click.Choice(['csv', 'json']), default='csv', help='Input file format')
@click.option('--id-field', default='id', help='Field name containing page IDs')
@click.option('--dry-run', is_flag=True, help='Preview operations without executing')
@click.option('--output', '-o', type=click.Choice(['json', 'table', 'yaml', 'text']), 
              default='table', help='Output format')
@click.pass_context
def update_pages(ctx, file_path: str, format: str, id_field: str, dry_run: bool, output: str):
    """Update multiple pages from a CSV or JSON file.
    
    The file must contain a field with page IDs to update.
    
    Example CSV format:
    id,title,status
    "page-id-1","Updated Title 1","Published"
    "page-id-2","Updated Title 2","Archived"
    """
    client = ctx.obj['client']
    
    try:
        # Load data from file
        data = load_data_from_file(file_path, format)
        console.print(f"Loaded {len(data)} items from {file_path}")
        
        # Validate that all items have IDs
        items_without_id = [item for item in data if not item.get(id_field)]
        if items_without_id:
            raise click.ClickException(f"{len(items_without_id)} items missing '{id_field}' field")
        
        if dry_run:
            console.print("\n[yellow]DRY RUN MODE - No changes will be made[/yellow]\n")
            
            # Show preview table
            table = Table(title="Pages to be updated")
            table.add_column("Page ID", style="cyan")
            table.add_column("Updates", style="green")
            
            for item in data[:10]:
                page_id = item[id_field]
                updates = {k: v for k, v in item.items() if k != id_field and v}
                table.add_row(page_id, str(updates))
            
            if len(data) > 10:
                table.add_row("...", f"({len(data) - 10} more items)")
            
            console.print(table)
            return
        
        # Confirm operation
        if not Confirm.ask(f"Update {len(data)} pages?"):
            console.print("Operation cancelled")
            return
        
        # Update pages with progress bar
        updated_pages = []
        failed_items = []
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=console
        ) as progress:
            task = progress.add_task("Updating pages...", total=len(data))
            
            for item in data:
                try:
                    page_id = item[id_field]
                    
                    # Build properties to update
                    properties = {}
                    for key, value in item.items():
                        if key != id_field and value:
                            # Handle special cases
                            if key.lower() == 'title':
                                properties['title'] = PropertyFactory.create_property('title', value)
                            elif key.lower() == 'archived' and value.lower() in ['true', 'false']:
                                # This would be handled separately as page archive status
                                pass
                            else:
                                # Simple text property for now
                                properties[key] = PropertyFactory.create_property('rich_text', value)
                    
                    # Update page
                    if properties:
                        result = client.update_page(page_id, properties=properties)
                        updated_pages.append({
                            'id': page_id,
                            'url': result.get('url', ''),
                            'updated_properties': list(properties.keys())
                        })
                    
                except Exception as e:
                    failed_items.append({
                        'id': item.get(id_field),
                        'error': str(e)
                    })
                
                progress.update(task, advance=1)
        
        # Show results
        console.print(f"\n✅ Successfully updated {len(updated_pages)} pages")
        
        if failed_items:
            console.print(f"❌ Failed to update {len(failed_items)} pages", style="red")
            for failed in failed_items[:5]:
                console.print(f"  - {failed['id']}: {failed['error']}")
            if len(failed_items) > 5:
                console.print(f"  ... and {len(failed_items) - 5} more")
        
        # Format output
        if output == 'json':
            click.echo(json.dumps({
                'updated': updated_pages,
                'failed': len(failed_items),
                'total': len(data)
            }, indent=2))
        elif output == 'table' and updated_pages:
            table = Table(title="Updated Pages")
            table.add_column("Page ID", style="cyan")
            table.add_column("Updated Properties", style="green")
            
            for page in updated_pages[:20]:
                table.add_row(page['id'], ', '.join(page['updated_properties']))
            
            if len(updated_pages) > 20:
                table.add_row("...", f"({len(updated_pages) - 20} more pages)")
            
            console.print(table)
        
    except Exception as e:
        raise click.ClickException(str(e))


@bulk.command()
@click.argument('file_path', type=click.Path(exists=True))
@click.option('--format', type=click.Choice(['csv', 'json']), default='csv', help='Input file format')
@click.option('--id-field', default='id', help='Field name containing page IDs')
@click.option('--dry-run', is_flag=True, help='Preview operations without executing')
@click.option('--force', is_flag=True, help='Skip confirmation prompt')
@click.pass_context
def delete_pages(ctx, file_path: str, format: str, id_field: str, dry_run: bool, force: bool):
    """Archive (delete) multiple pages from a CSV or JSON file.
    
    The file must contain a field with page IDs to delete.
    
    Example CSV format:
    id,reason
    "page-id-1","Obsolete content"
    "page-id-2","Duplicate page"
    """
    client = ctx.obj['client']
    
    try:
        # Load data from file
        data = load_data_from_file(file_path, format)
        console.print(f"Loaded {len(data)} items from {file_path}")
        
        # Extract page IDs
        page_ids = []
        for item in data:
            if isinstance(item, str):
                page_ids.append(item)
            elif isinstance(item, dict) and item.get(id_field):
                page_ids.append(item[id_field])
            else:
                console.print(f"Warning: Skipping item without '{id_field}' field: {item}")
        
        if not page_ids:
            raise click.ClickException("No valid page IDs found")
        
        console.print(f"Found {len(page_ids)} page IDs to archive")
        
        if dry_run:
            console.print("\n[yellow]DRY RUN MODE - No pages will be deleted[/yellow]\n")
            console.print("Page IDs that would be archived:")
            for page_id in page_ids[:10]:
                console.print(f"  - {page_id}")
            if len(page_ids) > 10:
                console.print(f"  ... and {len(page_ids) - 10} more")
            return
        
        # Confirm operation
        if not force and not Confirm.ask(
            f"[red]Archive {len(page_ids)} pages? This action cannot be undone![/red]"
        ):
            console.print("Operation cancelled")
            return
        
        # Archive pages with progress bar
        archived_pages = []
        failed_pages = []
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=console
        ) as progress:
            task = progress.add_task("Archiving pages...", total=len(page_ids))
            
            for page_id in page_ids:
                try:
                    # Archive the page
                    client.update_page(page_id, archived=True)
                    archived_pages.append(page_id)
                    
                except Exception as e:
                    failed_pages.append({
                        'id': page_id,
                        'error': str(e)
                    })
                
                progress.update(task, advance=1)
        
        # Show results
        console.print(f"\n✅ Successfully archived {len(archived_pages)} pages")
        
        if failed_pages:
            console.print(f"❌ Failed to archive {len(failed_pages)} pages", style="red")
            for failed in failed_pages[:5]:
                console.print(f"  - {failed['id']}: {failed['error']}")
            if len(failed_pages) > 5:
                console.print(f"  ... and {len(failed_pages) - 5} more")
        
        # Summary
        console.print(f"\nTotal processed: {len(page_ids)}")
        console.print(f"Archived: {len(archived_pages)}")
        console.print(f"Failed: {len(failed_pages)}")
        
    except Exception as e:
        raise click.ClickException(str(e))


@bulk.command()
@click.option('--parent-id', help='Parent page ID to list pages from')
@click.option('--database-id', help='Database ID to list pages from')
@click.option('--limit', default=100, help='Maximum number of pages to list')
@click.option('--output', '-o', type=click.Choice(['json', 'csv', 'table']), 
              default='table', help='Output format')
@click.option('--export-file', type=click.Path(), help='Export to file (for bulk operations)')
@click.pass_context
def list_pages(ctx, parent_id: Optional[str], database_id: Optional[str], 
               limit: int, output: str, export_file: Optional[str]):
    """List pages for bulk operations.
    
    Use this to export page IDs for bulk updates or deletes.
    """
    client = ctx.obj['client']
    
    if not parent_id and not database_id:
        raise click.ClickException("Either --parent-id or --database-id must be specified")
    
    try:
        pages = []
        
        if database_id:
            # Query database
            console.print(f"Querying database {database_id}...")
            results = client.query_database(database_id, page_size=limit)
            pages = results.get('results', [])
        else:
            # Search for child pages
            console.print(f"Searching for pages under {parent_id}...")
            # This is a simplified approach - in reality, we'd need to implement
            # a proper child page search
            results = client.search(filter={'property': 'object', 'value': 'page'})
            pages = [p for p in results.get('results', []) 
                    if p.get('parent', {}).get('page_id') == parent_id][:limit]
        
        console.print(f"Found {len(pages)} pages")
        
        # Prepare data for output
        page_data = []
        for page in pages:
            properties = page.get('properties', {})
            title_prop = properties.get('title', properties.get('Name', {}))
            title = ''
            if title_prop.get('title'):
                title = ''.join([t.get('plain_text', '') for t in title_prop['title']])
            
            page_data.append({
                'id': page['id'],
                'title': title,
                'created_time': page.get('created_time', ''),
                'last_edited_time': page.get('last_edited_time', ''),
                'url': page.get('url', '')
            })
        
        # Output results
        if export_file:
            # Export to file
            export_path = Path(export_file)
            if export_path.suffix == '.csv' or output == 'csv':
                with open(export_path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=['id', 'title', 'created_time', 
                                                          'last_edited_time', 'url'])
                    writer.writeheader()
                    writer.writerows(page_data)
            else:
                with open(export_path, 'w', encoding='utf-8') as f:
                    json.dump(page_data, f, indent=2)
            
            console.print(f"✅ Exported {len(page_data)} pages to {export_file}")
        
        elif output == 'json':
            click.echo(json.dumps(page_data, indent=2))
        
        elif output == 'csv':
            writer = csv.DictWriter(sys.stdout, fieldnames=['id', 'title', 'created_time', 
                                                           'last_edited_time', 'url'])
            writer.writeheader()
            writer.writerows(page_data)
        
        else:  # table
            table = Table(title="Pages")
            table.add_column("ID", style="cyan")
            table.add_column("Title", style="green")
            table.add_column("Created", style="yellow")
            
            for page in page_data[:50]:
                table.add_row(
                    page['id'],
                    page['title'] or "(Untitled)",
                    page['created_time'][:10] if page['created_time'] else ""
                )
            
            if len(page_data) > 50:
                table.add_row("...", f"({len(page_data) - 50} more pages)", "...")
            
            console.print(table)
        
    except Exception as e:
        raise click.ClickException(str(e))