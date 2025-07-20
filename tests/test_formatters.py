"""Tests for output formatters."""

import pytest
import json
import yaml
from notion_cli.formatters import (
    JSONFormatter, YAMLFormatter, TableFormatter,
    TextFormatter, get_formatter
)


class TestJSONFormatter:
    """Test JSON formatter."""
    
    def test_format_dict(self):
        """Test formatting a dictionary."""
        formatter = JSONFormatter(color=False)
        data = {"key": "value", "number": 42}
        result = formatter.format(data)
        
        assert json.loads(result) == data
    
    def test_format_list(self):
        """Test formatting a list."""
        formatter = JSONFormatter(color=False)
        data = [{"id": 1}, {"id": 2}]
        result = formatter.format(data)
        
        assert json.loads(result) == data


class TestYAMLFormatter:
    """Test YAML formatter."""
    
    def test_format_dict(self):
        """Test formatting a dictionary."""
        formatter = YAMLFormatter(color=False)
        data = {"key": "value", "number": 42}
        result = formatter.format(data)
        
        assert yaml.safe_load(result) == data
    
    def test_format_list(self):
        """Test formatting a list."""
        formatter = YAMLFormatter(color=False)
        data = [{"id": 1}, {"id": 2}]
        result = formatter.format(data)
        
        assert yaml.safe_load(result) == data


class TestTableFormatter:
    """Test table formatter."""
    
    def test_format_dict(self):
        """Test formatting a dictionary."""
        formatter = TableFormatter(color=False)
        data = {"key": "value", "number": 42}
        result = formatter.format(data)
        
        assert "key" in result
        assert "value" in result
        assert "42" in result
    
    def test_format_list_of_dicts(self):
        """Test formatting a list of dictionaries."""
        formatter = TableFormatter(color=False)
        data = [
            {"name": "Item 1", "status": "Done"},
            {"name": "Item 2", "status": "Todo"}
        ]
        result = formatter.format(data)
        
        assert "name" in result
        assert "status" in result
        assert "Item 1" in result
        assert "Done" in result
    
    def test_format_empty_list(self):
        """Test formatting an empty list."""
        formatter = TableFormatter(color=False)
        result = formatter.format([])
        
        assert result == "No data to display"


class TestTextFormatter:
    """Test text formatter."""
    
    def test_format_dict(self):
        """Test formatting a dictionary."""
        formatter = TextFormatter(color=False)
        data = {"key": "value", "nested": {"inner": "data"}}
        result = formatter.format(data)
        
        assert "key: value" in result
        assert "nested:" in result
        assert "inner: data" in result
    
    def test_format_list(self):
        """Test formatting a list."""
        formatter = TextFormatter(color=False)
        data = ["item1", "item2"]
        result = formatter.format(data)
        
        assert "1. item1" in result
        assert "2. item2" in result


def test_get_formatter():
    """Test get_formatter function."""
    json_formatter = get_formatter("json", color=False)
    assert isinstance(json_formatter, JSONFormatter)
    
    yaml_formatter = get_formatter("yaml", color=False)
    assert isinstance(yaml_formatter, YAMLFormatter)
    
    table_formatter = get_formatter("table", color=False)
    assert isinstance(table_formatter, TableFormatter)
    
    text_formatter = get_formatter("text", color=False)
    assert isinstance(text_formatter, TextFormatter)
    
    # Test default
    default_formatter = get_formatter("unknown", color=False)
    assert isinstance(default_formatter, JSONFormatter)