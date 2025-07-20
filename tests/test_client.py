"""Tests for Notion client."""

import pytest
from unittest.mock import Mock, patch
from notion_cli.client import NotionClient


class TestNotionClient:
    """Test NotionClient class."""
    
    def test_init_with_auth(self):
        """Test client initialization with auth parameter."""
        with patch("notion_cli.client.Client") as mock_client:
            client = NotionClient(auth="test-key")
            assert client.auth == "test-key"
            mock_client.assert_called_once_with(auth="test-key")
    
    def test_init_from_env(self):
        """Test client initialization from environment variable."""
        with patch("notion_cli.client.Client") as mock_client:
            with patch.dict("os.environ", {"NOTION_API_KEY": "env-key"}):
                client = NotionClient()
                assert client.auth == "env-key"
                mock_client.assert_called_once_with(auth="env-key")
    
    def test_init_no_auth_raises(self):
        """Test client initialization without auth raises error."""
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(ValueError, match="No API key provided"):
                NotionClient()
    
    def test_search(self):
        """Test search method."""
        with patch("notion_cli.client.Client") as mock_client:
            mock_instance = mock_client.return_value
            mock_instance.search.return_value = {
                "results": [{"id": "1"}, {"id": "2"}],
                "has_more": False
            }
            
            client = NotionClient(auth="test-key")
            results = client.search(query="test")
            
            assert len(results) == 2
            mock_instance.search.assert_called_with(
                query="test",
                page_size=100
            )
    
    def test_search_with_pagination(self):
        """Test search with pagination."""
        with patch("notion_cli.client.Client") as mock_client:
            mock_instance = mock_client.return_value
            
            # Mock _test_connection search call first
            mock_instance.search.side_effect = [
                # First call is from _test_connection
                {"results": [], "has_more": False},
                # Then the actual search calls with pagination
                {
                    "results": [{"id": "1"}, {"id": "2"}],
                    "has_more": True,
                    "next_cursor": "cursor1"
                },
                # Second page
                {
                    "results": [{"id": "3"}],
                    "has_more": False
                }
            ]
            
            client = NotionClient(auth="test-key")
            results = client.search(query="test")
            
            assert len(results) == 3
            assert results[0]["id"] == "1"
            assert results[2]["id"] == "3"
    
    def test_get_page(self):
        """Test get_page method."""
        with patch("notion_cli.client.Client") as mock_client:
            mock_instance = mock_client.return_value
            mock_instance.pages.retrieve.return_value = {"id": "page-123"}
            
            client = NotionClient(auth="test-key")
            page = client.get_page("page-123")
            
            assert page["id"] == "page-123"
            mock_instance.pages.retrieve.assert_called_with(page_id="page-123")
    
    def test_create_page_with_string_parent(self):
        """Test create_page with string parent ID."""
        with patch("notion_cli.client.Client") as mock_client:
            mock_instance = mock_client.return_value
            mock_instance.pages.create.return_value = {"id": "new-page"}
            
            client = NotionClient(auth="test-key")
            
            # Test with database ID format
            page = client.create_page(
                parent="897e5a76ae524b489fdfe71f5945d1af",
                properties={"title": {"title": [{"text": {"content": "Test"}}]}}
            )
            
            mock_instance.pages.create.assert_called_with(
                parent={"database_id": "897e5a76ae524b489fdfe71f5945d1af"},
                properties={"title": {"title": [{"text": {"content": "Test"}}]}}
            )
    
    def test_query_database(self):
        """Test query_database method."""
        with patch("notion_cli.client.Client") as mock_client:
            mock_instance = mock_client.return_value
            mock_instance.databases.query.return_value = {
                "results": [{"id": "1"}],
                "has_more": False
            }
            
            client = NotionClient(auth="test-key")
            results = client.query_database(
                "db-123",
                filter={"property": "Status", "select": {"equals": "Done"}}
            )
            
            assert len(results) == 1
            mock_instance.databases.query.assert_called_with(
                database_id="db-123",
                page_size=100,
                filter={"property": "Status", "select": {"equals": "Done"}}
            )