"""Pytest configuration and fixtures."""

import pytest
from unittest.mock import Mock, MagicMock
from notion_cli.client import NotionClient
from notion_cli.config import Config


@pytest.fixture
def mock_notion_client():
    """Mock Notion client for testing."""
    mock = Mock(spec=NotionClient)
    
    # Mock common methods
    mock.search.return_value = []
    mock.get_page.return_value = {
        "object": "page",
        "id": "test-page-id",
        "properties": {
            "title": {
                "type": "title",
                "title": [{"plain_text": "Test Page"}]
            }
        }
    }
    mock.list_databases.return_value = []
    mock.query_database.return_value = []
    
    return mock


@pytest.fixture
def mock_config():
    """Mock configuration for testing."""
    config = Mock(spec=Config)
    config.api_key = "test-api-key"
    config.output_format = "json"
    config.color_output = False
    config.page_size = 100
    config.get.side_effect = lambda key, default=None: {
        "api_key": "test-api-key",
        "output_format": "json",
        "color_output": False,
        "page_size": 100
    }.get(key, default)
    
    return config


@pytest.fixture
def test_page_data():
    """Sample page data for testing."""
    return {
        "object": "page",
        "id": "550dc4b7-6cdb-4a73-8a90-b86b3a8c9b06",
        "created_time": "2024-01-01T00:00:00.000Z",
        "last_edited_time": "2024-01-01T12:00:00.000Z",
        "archived": False,
        "url": "https://www.notion.so/Test-Page-550dc4b76cdb4a738a90b86b3a8c9b06",
        "properties": {
            "Name": {
                "id": "title",
                "type": "title",
                "title": [{
                    "type": "text",
                    "text": {"content": "Test Page"},
                    "plain_text": "Test Page"
                }]
            },
            "Status": {
                "id": "status",
                "type": "select",
                "select": {
                    "id": "1",
                    "name": "In Progress",
                    "color": "yellow"
                }
            }
        }
    }


@pytest.fixture
def test_database_data():
    """Sample database data for testing."""
    return {
        "object": "database",
        "id": "897e5a76-ae52-4b48-9fdf-e71f5945d1af",
        "created_time": "2024-01-01T00:00:00.000Z",
        "last_edited_time": "2024-01-01T12:00:00.000Z",
        "title": [{
            "type": "text",
            "text": {"content": "Test Database"},
            "plain_text": "Test Database"
        }],
        "properties": {
            "Name": {
                "id": "title",
                "type": "title",
                "title": {}
            },
            "Status": {
                "id": "status",
                "type": "select",
                "select": {
                    "options": [
                        {"id": "1", "name": "To Do", "color": "gray"},
                        {"id": "2", "name": "In Progress", "color": "yellow"},
                        {"id": "3", "name": "Done", "color": "green"}
                    ]
                }
            },
            "Priority": {
                "id": "priority",
                "type": "select",
                "select": {
                    "options": [
                        {"id": "1", "name": "Low", "color": "gray"},
                        {"id": "2", "name": "Medium", "color": "yellow"},
                        {"id": "3", "name": "High", "color": "red"}
                    ]
                }
            }
        }
    }