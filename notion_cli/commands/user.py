"""User management commands for Notion CLI."""
import click
from rich.console import Console
from rich.table import Table
from typing import Optional

from ..client import NotionClient
from ..utils.formatting import format_output

console = Console()


@click.group()
@click.pass_context
def user(ctx):
    """Manage Notion workspace users."""
    ctx.ensure_object(dict)
    ctx.obj['client'] = NotionClient()


@user.command()
@click.option('--output', '-o', type=click.Choice(['json', 'table', 'yaml', 'text']), 
              default='table', help='Output format')
@click.option('--limit', type=int, help='Maximum number of users to retrieve')
@click.pass_context
def list(ctx, output: str, limit: Optional[int]):
    """List all users in the workspace.
    
    Examples:
        notion-cli user list
        notion-cli user list --output json
        notion-cli user list --limit 10
    """
    client = ctx.obj['client']
    
    try:
        # Get all users
        users = client.list_users()
        
        if limit and limit > 0:
            users = users[:limit]
        
        if not users:
            console.print("No users found in workspace")
            return
        
        # Format output
        if output == 'json':
            import json
            click.echo(json.dumps(users, indent=2))
        
        elif output == 'yaml':
            import yaml
            click.echo(yaml.dump(users, default_flow_style=False))
        
        elif output == 'table':
            table = Table(title=f"Workspace Users ({len(users)} total)")
            table.add_column("ID", style="cyan")
            table.add_column("Name", style="green")
            table.add_column("Email", style="blue")
            table.add_column("Type", style="yellow")
            table.add_column("Bot", style="magenta")
            
            for user_data in users:
                user_id = user_data.get('id', '')
                name = user_data.get('name', 'Unknown')
                email = user_data.get('person', {}).get('email', 'N/A') if user_data.get('type') == 'person' else 'N/A'
                user_type = user_data.get('type', 'unknown')
                is_bot = '✓' if user_data.get('bot') else '✗'
                
                table.add_row(user_id, name, email, user_type, is_bot)
            
            console.print(table)
        
        else:  # text
            for user_data in users:
                name = user_data.get('name', 'Unknown')
                user_id = user_data.get('id', '')
                user_type = user_data.get('type', 'unknown')
                console.print(f"{name} ({user_type}) - {user_id}")
        
    except Exception as e:
        raise click.ClickException(f"Failed to list users: {str(e)}")


@user.command()
@click.argument('user_id')
@click.option('--output', '-o', type=click.Choice(['json', 'table', 'yaml', 'text']), 
              default='json', help='Output format')
@click.pass_context
def get(ctx, user_id: str, output: str):
    """Get details for a specific user.
    
    USER_ID is the Notion user ID to retrieve.
    
    Examples:
        notion-cli user get 12345678-1234-1234-1234-123456789012
        notion-cli user get 12345678-1234-1234-1234-123456789012 --output table
    """
    client = ctx.obj['client']
    
    try:
        # Get user details
        user_data = client.get_user(user_id)
        
        # Format output
        if output == 'json':
            import json
            click.echo(json.dumps(user_data, indent=2))
        
        elif output == 'yaml':
            import yaml
            click.echo(yaml.dump(user_data, default_flow_style=False))
        
        elif output == 'table':
            table = Table(title="User Details")
            table.add_column("Property", style="cyan")
            table.add_column("Value", style="green")
            
            # Basic info
            table.add_row("ID", user_data.get('id', ''))
            table.add_row("Name", user_data.get('name', 'Unknown'))
            table.add_row("Type", user_data.get('type', 'unknown'))
            table.add_row("Object", user_data.get('object', ''))
            
            # Person-specific info
            if user_data.get('type') == 'person':
                person = user_data.get('person', {})
                table.add_row("Email", person.get('email', 'N/A'))
            
            # Bot info
            if user_data.get('bot'):
                bot = user_data.get('bot', {})
                table.add_row("Bot Type", "Yes")
                if isinstance(bot, dict):
                    table.add_row("Bot Owner", str(bot.get('owner', {}).get('type', 'N/A')))
            
            # Avatar
            if user_data.get('avatar_url'):
                table.add_row("Avatar URL", user_data['avatar_url'])
            
            console.print(table)
        
        else:  # text
            name = user_data.get('name', 'Unknown')
            user_type = user_data.get('type', 'unknown')
            user_id = user_data.get('id', '')
            console.print(f"User: {name}")
            console.print(f"Type: {user_type}")
            console.print(f"ID: {user_id}")
            
            if user_data.get('type') == 'person':
                email = user_data.get('person', {}).get('email', 'N/A')
                console.print(f"Email: {email}")
            
            if user_data.get('bot'):
                console.print("Bot: Yes")
        
    except Exception as e:
        raise click.ClickException(f"Failed to get user: {str(e)}")


@user.command()
@click.option('--output', '-o', type=click.Choice(['json', 'table', 'yaml', 'text']), 
              default='json', help='Output format')
@click.pass_context
def me(ctx, output: str):
    """Get information about the current bot/integration user.
    
    This shows details about the integration or bot that's making the API calls.
    
    Examples:
        notion-cli user me
        notion-cli user me --output table
    """
    client = ctx.obj['client']
    
    try:
        # Get current user info
        user_data = client.get_self()
        
        # Format output
        if output == 'json':
            import json
            click.echo(json.dumps(user_data, indent=2))
        
        elif output == 'yaml':
            import yaml
            click.echo(yaml.dump(user_data, default_flow_style=False))
        
        elif output == 'table':
            table = Table(title="Current Integration User")
            table.add_column("Property", style="cyan")
            table.add_column("Value", style="green")
            
            # Basic info
            table.add_row("ID", user_data.get('id', ''))
            table.add_row("Name", user_data.get('name', 'Unknown'))
            table.add_row("Type", user_data.get('type', 'unknown'))
            table.add_row("Object", user_data.get('object', ''))
            
            # Bot info
            if user_data.get('bot'):
                bot = user_data.get('bot', {})
                table.add_row("Bot Type", "Integration")
                if isinstance(bot, dict):
                    owner = bot.get('owner', {})
                    if owner.get('type') == 'workspace':
                        table.add_row("Bot Owner", "Workspace")
                        table.add_row("Workspace", str(owner.get('workspace', 'true')))
                    else:
                        table.add_row("Bot Owner", str(owner.get('type', 'Unknown')))
                    
                    # Workspace details
                    workspace_name = bot.get('workspace_name')
                    if workspace_name:
                        table.add_row("Workspace Name", workspace_name)
            
            # Avatar
            if user_data.get('avatar_url'):
                table.add_row("Avatar URL", user_data['avatar_url'])
            
            console.print(table)
        
        else:  # text
            name = user_data.get('name', 'Unknown')
            user_type = user_data.get('type', 'unknown')
            user_id = user_data.get('id', '')
            console.print(f"Integration: {name}")
            console.print(f"Type: {user_type}")
            console.print(f"ID: {user_id}")
            
            if user_data.get('bot'):
                bot = user_data.get('bot', {})
                if isinstance(bot, dict):
                    workspace_name = bot.get('workspace_name')
                    if workspace_name:
                        console.print(f"Workspace: {workspace_name}")
        
    except Exception as e:
        raise click.ClickException(f"Failed to get current user: {str(e)}")


@user.command()
@click.argument('query')
@click.option('--output', '-o', type=click.Choice(['json', 'table', 'yaml', 'text']), 
              default='table', help='Output format')
@click.pass_context
def search(ctx, query: str, output: str):
    """Search for users by name or email.
    
    QUERY is the search term to match against user names or emails.
    
    Examples:
        notion-cli user search john
        notion-cli user search "john.doe@example.com"
        notion-cli user search admin --output json
    """
    client = ctx.obj['client']
    
    try:
        # Get all users and filter
        all_users = client.list_users()
        
        # Search in name and email
        matching_users = []
        query_lower = query.lower()
        
        for user_data in all_users:
            name = user_data.get('name', '').lower()
            email = ''
            if user_data.get('type') == 'person':
                email = user_data.get('person', {}).get('email', '').lower()
            
            if query_lower in name or query_lower in email:
                matching_users.append(user_data)
        
        if not matching_users:
            console.print(f"No users found matching '{query}'")
            return
        
        # Format output
        if output == 'json':
            import json
            click.echo(json.dumps(matching_users, indent=2))
        
        elif output == 'yaml':
            import yaml
            click.echo(yaml.dump(matching_users, default_flow_style=False))
        
        elif output == 'table':
            table = Table(title=f"Users matching '{query}' ({len(matching_users)} found)")
            table.add_column("ID", style="cyan")
            table.add_column("Name", style="green")
            table.add_column("Email", style="blue")
            table.add_column("Type", style="yellow")
            
            for user_data in matching_users:
                user_id = user_data.get('id', '')
                name = user_data.get('name', 'Unknown')
                email = user_data.get('person', {}).get('email', 'N/A') if user_data.get('type') == 'person' else 'N/A'
                user_type = user_data.get('type', 'unknown')
                
                table.add_row(user_id, name, email, user_type)
            
            console.print(table)
        
        else:  # text
            console.print(f"Found {len(matching_users)} users matching '{query}':\n")
            for user_data in matching_users:
                name = user_data.get('name', 'Unknown')
                user_id = user_data.get('id', '')
                user_type = user_data.get('type', 'unknown')
                console.print(f"{name} ({user_type}) - {user_id}")
        
    except Exception as e:
        raise click.ClickException(f"Failed to search users: {str(e)}")