"""Output formatters for different display formats."""

import json
import yaml
from typing import Any, Dict, List, Union
from datetime import datetime
from tabulate import tabulate
from rich.console import Console
from rich.table import Table
from rich.syntax import Syntax
from rich.panel import Panel
from rich.text import Text


class OutputFormatter:
    """Base class for output formatters."""
    
    def __init__(self, color: bool = True):
        """Initialize formatter.
        
        Args:
            color: Whether to use colored output
        """
        self.color = color
        self.console = Console(force_terminal=color)
    
    def format(self, data: Any) -> str:
        """Format data for output.
        
        Args:
            data: Data to format
            
        Returns:
            Formatted string
        """
        raise NotImplementedError


class JSONFormatter(OutputFormatter):
    """JSON output formatter."""
    
    def format(self, data: Any) -> str:
        """Format data as JSON."""
        json_str = json.dumps(data, indent=2, default=str)
        
        if self.color:
            syntax = Syntax(json_str, "json", theme="monokai")
            return syntax
        return json_str


class YAMLFormatter(OutputFormatter):
    """YAML output formatter."""
    
    def format(self, data: Any) -> str:
        """Format data as YAML."""
        yaml_str = yaml.dump(data, default_flow_style=False, allow_unicode=True)
        
        if self.color:
            syntax = Syntax(yaml_str, "yaml", theme="monokai")
            return syntax
        return yaml_str


class TableFormatter(OutputFormatter):
    """Table output formatter."""
    
    def format(self, data: Any) -> str:
        """Format data as a table."""
        if isinstance(data, dict):
            # Single item - format as key-value pairs
            return self._format_dict(data)
        elif isinstance(data, list):
            if not data:
                return "No data to display"
            
            # Multiple items - format as table
            if isinstance(data[0], dict):
                return self._format_list_of_dicts(data)
            else:
                return self._format_list(data)
        else:
            return str(data)
    
    def _format_dict(self, data: Dict[str, Any]) -> str:
        """Format a dictionary as a key-value table."""
        if self.color:
            table = Table(show_header=False, box=None)
            table.add_column("Key", style="cyan", no_wrap=True)
            table.add_column("Value")
            
            for key, value in data.items():
                table.add_row(key, self._format_value(value))
            
            return table
        else:
            rows = [[key, self._format_value(value)] for key, value in data.items()]
            return tabulate(rows, headers=["Key", "Value"], tablefmt="simple")
    
    def _format_list_of_dicts(self, data: List[Dict[str, Any]]) -> str:
        """Format a list of dictionaries as a table."""
        if not data:
            return "No data"
        
        # Extract headers from first item
        headers = list(data[0].keys())
        
        if self.color:
            table = Table()
            for header in headers:
                table.add_column(header, style="cyan")
            
            for item in data:
                row = [self._format_value(item.get(h, "")) for h in headers]
                table.add_row(*row)
            
            return table
        else:
            rows = []
            for item in data:
                row = [self._format_value(item.get(h, "")) for h in headers]
                rows.append(row)
            
            return tabulate(rows, headers=headers, tablefmt="grid")
    
    def _format_list(self, data: List[Any]) -> str:
        """Format a simple list."""
        if self.color:
            return "\n".join([f"• {self._format_value(item)}" for item in data])
        else:
            return "\n".join([f"- {self._format_value(item)}" for item in data])
    
    def _format_value(self, value: Any) -> str:
        """Format a single value."""
        if value is None:
            return ""
        elif isinstance(value, bool):
            return "✓" if value else "✗" if self.color else str(value)
        elif isinstance(value, (list, dict)):
            return json.dumps(value, default=str)
        elif isinstance(value, datetime):
            return value.strftime("%Y-%m-%d %H:%M:%S")
        else:
            return str(value)


class TextFormatter(OutputFormatter):
    """Plain text output formatter."""
    
    def format(self, data: Any) -> str:
        """Format data as plain text."""
        if isinstance(data, dict):
            return self._format_dict(data)
        elif isinstance(data, list):
            return self._format_list(data)
        else:
            return str(data)
    
    def _format_dict(self, data: Dict[str, Any], indent: int = 0) -> str:
        """Format a dictionary as plain text."""
        lines = []
        indent_str = "  " * indent
        
        for key, value in data.items():
            if isinstance(value, dict):
                lines.append(f"{indent_str}{key}:")
                lines.append(self._format_dict(value, indent + 1))
            elif isinstance(value, list):
                lines.append(f"{indent_str}{key}:")
                for item in value:
                    if isinstance(item, dict):
                        lines.append(self._format_dict(item, indent + 1))
                    else:
                        lines.append(f"{indent_str}  - {item}")
            else:
                lines.append(f"{indent_str}{key}: {value}")
        
        return "\n".join(lines)
    
    def _format_list(self, data: List[Any]) -> str:
        """Format a list as plain text."""
        lines = []
        
        for i, item in enumerate(data):
            if isinstance(item, dict):
                lines.append(f"\n--- Item {i + 1} ---")
                lines.append(self._format_dict(item))
            else:
                lines.append(f"{i + 1}. {item}")
        
        return "\n".join(lines)


class NotionDataFormatter:
    """Specialized formatter for Notion data structures."""
    
    def __init__(self, formatter: OutputFormatter):
        """Initialize with a base formatter."""
        self.formatter = formatter
        self.console = formatter.console
    
    def format_page(self, page: Dict[str, Any]) -> Any:
        """Format a Notion page."""
        simplified = {
            "id": page.get("id"),
            "created_time": page.get("created_time"),
            "last_edited_time": page.get("last_edited_time"),
            "archived": page.get("archived", False),
            "url": page.get("url"),
            "properties": self._simplify_properties(page.get("properties", {}))
        }
        
        if page.get("parent"):
            simplified["parent"] = self._simplify_parent(page["parent"])
        
        return self.formatter.format(simplified)
    
    def format_database(self, database: Dict[str, Any]) -> Any:
        """Format a Notion database."""
        simplified = {
            "id": database.get("id"),
            "title": self._get_title_from_rich_text(database.get("title", [])),
            "created_time": database.get("created_time"),
            "last_edited_time": database.get("last_edited_time"),
            "archived": database.get("archived", False),
            "url": database.get("url"),
            "properties": self._simplify_database_properties(database.get("properties", {}))
        }
        
        if database.get("parent"):
            simplified["parent"] = self._simplify_parent(database["parent"])
        
        return self.formatter.format(simplified)
    
    def format_search_results(self, results: List[Dict[str, Any]]) -> Any:
        """Format search results."""
        simplified = []
        
        for result in results:
            item = {
                "type": result.get("object"),
                "id": result.get("id"),
                "url": result.get("url"),
                "last_edited": result.get("last_edited_time", "")[:10],  # Date only
            }
            
            # Extract title
            if result["object"] == "database":
                item["title"] = self._get_title_from_rich_text(result.get("title", []))
            else:  # page
                props = result.get("properties", {})
                for prop_value in props.values():
                    if prop_value.get("type") == "title":
                        item["title"] = self._get_title_from_property(prop_value)
                        break
                else:
                    item["title"] = "Untitled"
            
            simplified.append(item)
        
        return self.formatter.format(simplified)
    
    def format_blocks(self, blocks: List[Dict[str, Any]]) -> Any:
        """Format blocks."""
        simplified = []
        
        for block in blocks:
            item = {
                "type": block.get("type"),
                "id": block.get("id"),
                "content": self._extract_block_content(block)
            }
            
            if block.get("has_children"):
                item["has_children"] = True
            
            simplified.append(item)
        
        return self.formatter.format(simplified)
    
    def _simplify_properties(self, properties: Dict[str, Any]) -> Dict[str, Any]:
        """Simplify Notion properties to readable format."""
        simplified = {}
        
        for name, prop in properties.items():
            prop_type = prop.get("type")
            
            if prop_type == "title":
                simplified[name] = self._get_title_from_property(prop)
            elif prop_type == "rich_text":
                simplified[name] = self._get_text_from_rich_text(prop.get("rich_text", []))
            elif prop_type == "number":
                simplified[name] = prop.get("number")
            elif prop_type == "select":
                select = prop.get("select")
                simplified[name] = select.get("name") if select else None
            elif prop_type == "multi_select":
                simplified[name] = [s.get("name") for s in prop.get("multi_select", [])]
            elif prop_type == "date":
                date = prop.get("date")
                simplified[name] = date.get("start") if date else None
            elif prop_type == "checkbox":
                simplified[name] = prop.get("checkbox", False)
            elif prop_type == "url":
                simplified[name] = prop.get("url")
            elif prop_type == "email":
                simplified[name] = prop.get("email")
            elif prop_type == "phone_number":
                simplified[name] = prop.get("phone_number")
            elif prop_type == "relation":
                simplified[name] = [r.get("id") for r in prop.get("relation", [])]
            elif prop_type == "people":
                simplified[name] = [p.get("name", p.get("id")) for p in prop.get("people", [])]
            else:
                simplified[name] = prop
        
        return simplified
    
    def _simplify_database_properties(self, properties: Dict[str, Any]) -> Dict[str, Any]:
        """Simplify database schema properties."""
        simplified = {}
        
        for name, prop in properties.items():
            simplified[name] = {
                "type": prop.get("type"),
                "id": prop.get("id")
            }
            
            # Add type-specific info
            if prop["type"] == "select":
                simplified[name]["options"] = [
                    opt.get("name") for opt in prop.get("select", {}).get("options", [])
                ]
            elif prop["type"] == "multi_select":
                simplified[name]["options"] = [
                    opt.get("name") for opt in prop.get("multi_select", {}).get("options", [])
                ]
            elif prop["type"] == "relation":
                rel = prop.get("relation", {})
                simplified[name]["database_id"] = rel.get("database_id")
        
        return simplified
    
    def _simplify_parent(self, parent: Dict[str, Any]) -> Dict[str, Any]:
        """Simplify parent reference."""
        parent_type = parent.get("type")
        return {
            "type": parent_type,
            "id": parent.get(f"{parent_type}_id") or parent.get(parent_type)
        }
    
    def _get_title_from_property(self, prop: Dict[str, Any]) -> str:
        """Extract title from a title property."""
        title_array = prop.get("title", [])
        return self._get_text_from_rich_text(title_array)
    
    def _get_title_from_rich_text(self, rich_text: List[Dict[str, Any]]) -> str:
        """Extract plain text from rich text array."""
        return self._get_text_from_rich_text(rich_text)
    
    def _get_text_from_rich_text(self, rich_text: List[Dict[str, Any]]) -> str:
        """Extract plain text from rich text array."""
        if not rich_text:
            return ""
        return "".join([t.get("plain_text", "") for t in rich_text])
    
    def _extract_block_content(self, block: Dict[str, Any]) -> str:
        """Extract content from a block."""
        block_type = block.get("type")
        block_data = block.get(block_type, {})
        
        # Handle text-based blocks
        if "rich_text" in block_data:
            return self._get_text_from_rich_text(block_data.get("rich_text", []))
        elif "caption" in block_data:
            return self._get_text_from_rich_text(block_data.get("caption", []))
        elif block_type == "code":
            return f"[{block_data.get('language', 'plain')}] {self._get_text_from_rich_text(block_data.get('rich_text', []))}"
        elif block_type in ["image", "video", "file", "pdf"]:
            file_data = block_data.get(block_data.get("type"), {})
            return file_data.get("url", "")
        else:
            return f"[{block_type} block]"


def get_formatter(format_type: str, color: bool = True) -> OutputFormatter:
    """Get a formatter instance by type.
    
    Args:
        format_type: One of 'json', 'yaml', 'table', 'text'
        color: Whether to use colored output
        
    Returns:
        Formatter instance
    """
    formatters = {
        "json": JSONFormatter,
        "yaml": YAMLFormatter,
        "table": TableFormatter,
        "text": TextFormatter,
    }
    
    formatter_class = formatters.get(format_type.lower(), JSONFormatter)
    return formatter_class(color=color)