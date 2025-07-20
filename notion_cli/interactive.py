"""Interactive mode for Notion CLI."""

import click
import shlex
from typing import Optional, List
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter, Completer, Completion
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.styles import Style
from rich.console import Console
from pathlib import Path

from .client import NotionClient
from .config import Config
from .cli import handle_error


console = Console()


class NotionCompleter(Completer):
    """Custom completer for Notion CLI commands."""
    
    def __init__(self):
        self.commands = {
            "search": ["--type", "--limit", "--sort", "--output"],
            "page": {
                "get": ["--output"],
                "create": ["--title", "--parent", "--property", "--content", "--icon", "--cover", "--output"],
                "update": ["--title", "--property", "--archived", "--icon", "--cover", "--output"],
                "delete": ["--confirm"],
                "search": ["--limit", "--output"],
                "export": ["--format", "--output-file", "--include-children"]
            },
            "database": {
                "list": ["--output"],
                "get": ["--output"],
                "query": ["--filter", "--sort", "--limit", "--output"],
                "create-page": ["--property", "--output"],
                "export": ["--format", "--output-file", "--filter"],
                "create": ["--parent", "--title", "--schema", "--output"]
            },
            "block": {
                "children": ["--limit", "--output"],
                "append": ["--text", "--heading", "--bullet", "--number", "--todo", "--code", "--quote", "--divider", "--output"],
                "update": ["--text", "--checked", "--output"],
                "delete": ["--confirm"]
            },
            "config": {
                "init": [],
                "show": ["--output"],
                "set": [],
                "get": [],
                "unset": ["--confirm"],
                "path": [],
                "edit": ["--editor"]
            },
            "bulk": ["--filter", "--set", "--output", "--dry-run"],
            "help": [],
            "exit": [],
            "quit": [],
            "clear": []
        }
    
    def get_completions(self, document, complete_event):
        """Get completions based on current input."""
        text = document.text_before_cursor.lstrip()
        words = text.split()
        
        if not words:
            # Complete top-level commands
            for cmd in self.commands.keys():
                yield Completion(cmd, start_position=0)
        elif len(words) == 1:
            # Complete commands that start with current word
            for cmd in self.commands.keys():
                if cmd.startswith(words[0]):
                    yield Completion(cmd, start_position=-len(words[0]))
        elif len(words) == 2 and words[0] in ["page", "database", "block", "config"]:
            # Complete subcommands
            if isinstance(self.commands[words[0]], dict):
                for subcmd in self.commands[words[0]].keys():
                    if subcmd.startswith(words[1]):
                        yield Completion(subcmd, start_position=-len(words[1]))
        else:
            # Complete options
            cmd_path = words[0]
            if len(words) >= 2 and words[0] in ["page", "database", "block", "config"]:
                cmd_path = f"{words[0]}.{words[1]}"
                options = self.commands.get(words[0], {}).get(words[1], [])
            else:
                options = self.commands.get(cmd_path, [])
            
            current_word = words[-1] if words else ""
            
            # If current word starts with -, complete options
            if current_word.startswith("-"):
                for opt in options:
                    if opt.startswith(current_word):
                        yield Completion(opt, start_position=-len(current_word))
            else:
                # Complete options that haven't been used
                used_options = {w for w in words if w.startswith("-")}
                for opt in options:
                    if opt not in used_options:
                        yield Completion(opt, start_position=0)


@click.command()
@click.pass_context
def interactive_mode(ctx: click.Context):
    """Start interactive mode for Notion CLI.
    
    This mode provides an interactive prompt with:
    - Command completion
    - Command history
    - Syntax highlighting
    - Auto-suggestions
    
    Type 'help' for available commands or 'exit' to quit.
    """
    config = ctx.obj["config"]
    
    # Print welcome message
    console.print("[bold blue]Notion CLI Interactive Mode[/bold blue]")
    console.print("Type 'help' for commands, 'exit' to quit\n")
    
    # Set up prompt session
    history_file = Path.home() / ".notion-cli" / "history"
    history_file.parent.mkdir(parents=True, exist_ok=True)
    
    session = PromptSession(
        history=FileHistory(str(history_file)),
        auto_suggest=AutoSuggestFromHistory(),
        completer=NotionCompleter(),
        style=Style.from_dict({
            'prompt': '#00aa00 bold',
        })
    )
    
    # Initialize client once
    try:
        client = NotionClient(config.api_key)
    except Exception as e:
        console.print(f"[red]Failed to initialize Notion client: {e}[/red]")
        return
    
    # Store client in context for commands
    ctx.obj["client"] = client
    
    # Interactive loop
    while True:
        try:
            # Get input
            command_line = session.prompt("notion> ", style=Style.from_dict({'': '#00aa00'}))
            
            if not command_line.strip():
                continue
            
            # Parse command
            try:
                args = shlex.split(command_line)
            except ValueError as e:
                console.print(f"[red]Invalid command: {e}[/red]")
                continue
            
            if not args:
                continue
            
            # Handle built-in commands
            if args[0] in ["exit", "quit"]:
                console.print("Goodbye! 👋")
                break
            elif args[0] == "clear":
                console.clear()
                continue
            elif args[0] == "help":
                show_interactive_help()
                continue
            
            # Execute command
            from .cli import cli as main_cli
            
            try:
                # Create a new context with our config
                main_cli.main(args, standalone_mode=False, obj=ctx.obj)
            except SystemExit:
                # Catch system exit from Click
                pass
            except Exception as e:
                handle_error(e, config.get("debug", False))
            
        except KeyboardInterrupt:
            console.print("\n[yellow]Use 'exit' to quit[/yellow]")
            continue
        except EOFError:
            console.print("\nGoodbye! 👋")
            break


def show_interactive_help():
    """Show help for interactive mode."""
    help_text = """
[bold]Available Commands:[/bold]

[cyan]Search & Navigation:[/cyan]
  search [query]           Search across your workspace
  page search [query]      Search for pages
  database list            List all databases

[cyan]Page Commands:[/cyan]
  page get <id>            Get page details
  page create              Create a new page
  page update <id>         Update a page
  page delete <id>         Delete (archive) a page
  page export <id>         Export page content

[cyan]Database Commands:[/cyan]
  database get <id>        Get database info
  database query <id>      Query database with filters
  database create-page <id> Create entry in database
  database export <id>     Export database to CSV/JSON

[cyan]Block Commands:[/cyan]
  block children <id>      Get child blocks
  block append <id>        Add content to page
  block update <id>        Update a block
  block delete <id>        Delete a block

[cyan]Configuration:[/cyan]
  config show              Show current config
  config set <key> <val>   Set config value
  config get <key>         Get config value

[cyan]Other Commands:[/cyan]
  bulk                     Bulk operations
  help                     Show this help
  clear                    Clear screen
  exit/quit                Exit interactive mode

[dim]Tips:[/dim]
  • Use Tab for command completion
  • Use ↑/↓ for command history
  • IDs can be partial (first 8+ chars)
  • Use --output to change format (json/yaml/table/text)
"""
    console.print(help_text)