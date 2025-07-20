"""Core Notion client wrapper with enhanced functionality."""

import os
from typing import Dict, List, Optional, Any, Union
from notion_client import Client
from notion_client.errors import APIResponseError
import logging

logger = logging.getLogger(__name__)


class NotionClient:
    """Enhanced Notion client with convenience methods."""
    
    def __init__(self, auth: Optional[str] = None):
        """Initialize the Notion client.
        
        Args:
            auth: Notion API key. If not provided, will look for NOTION_API_KEY env var.
        """
        self.auth = auth or os.getenv("NOTION_API_KEY")
        if not self.auth:
            raise ValueError(
                "No API key provided. Set NOTION_API_KEY environment variable or pass auth parameter."
            )
        
        self.client = Client(auth=self.auth)
        self._test_connection()
    
    def _test_connection(self) -> None:
        """Test the API connection."""
        try:
            self.client.search(query="", page_size=1)
            logger.info("Successfully connected to Notion API")
        except APIResponseError as e:
            raise ConnectionError(f"Failed to connect to Notion API: {e}")
    
    # ===== SEARCH METHODS =====
    
    def search(
        self,
        query: str = "",
        filter_type: Optional[str] = None,
        sort: Optional[Dict[str, str]] = None,
        page_size: int = 100
    ) -> List[Dict[str, Any]]:
        """Search for pages and databases.
        
        Args:
            query: Search query string
            filter_type: Filter by 'page' or 'database'
            sort: Sort criteria
            page_size: Number of results per page
            
        Returns:
            List of search results
        """
        params = {
            "query": query,
            "page_size": page_size
        }
        
        if filter_type:
            params["filter"] = {"property": "object", "value": filter_type}
        
        if sort:
            params["sort"] = sort
        
        results = []
        has_more = True
        start_cursor = None
        
        while has_more:
            if start_cursor:
                params["start_cursor"] = start_cursor
            
            response = self.client.search(**params)
            results.extend(response["results"])
            
            has_more = response.get("has_more", False)
            start_cursor = response.get("next_cursor")
        
        return results
    
    # ===== PAGE METHODS =====
    
    def get_page(self, page_id: str) -> Dict[str, Any]:
        """Retrieve a page by ID."""
        return self.client.pages.retrieve(page_id=page_id)
    
    def create_page(
        self,
        parent: Union[str, Dict[str, str]],
        properties: Dict[str, Any],
        children: Optional[List[Dict[str, Any]]] = None,
        icon: Optional[Dict[str, Any]] = None,
        cover: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a new page.
        
        Args:
            parent: Parent page/database ID or dict with type and ID
            properties: Page properties
            children: Optional list of block children
            icon: Optional icon
            cover: Optional cover image
            
        Returns:
            Created page object
        """
        # Handle parent as string ID
        if isinstance(parent, str):
            # Determine if it's a database or page ID
            if len(parent) == 32 or "-" not in parent:
                parent = {"database_id": parent}
            else:
                parent = {"page_id": parent}
        
        params = {
            "parent": parent,
            "properties": properties
        }
        
        if children:
            params["children"] = children
        if icon:
            params["icon"] = icon
        if cover:
            params["cover"] = cover
        
        return self.client.pages.create(**params)
    
    def update_page(
        self,
        page_id: str,
        properties: Optional[Dict[str, Any]] = None,
        archived: Optional[bool] = None,
        icon: Optional[Dict[str, Any]] = None,
        cover: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Update a page."""
        params = {}
        
        if properties:
            params["properties"] = properties
        if archived is not None:
            params["archived"] = archived
        if icon:
            params["icon"] = icon
        if cover:
            params["cover"] = cover
        
        return self.client.pages.update(page_id=page_id, **params)
    
    def delete_page(self, page_id: str) -> Dict[str, Any]:
        """Delete (archive) a page."""
        return self.update_page(page_id, archived=True)
    
    # ===== DATABASE METHODS =====
    
    def list_databases(self) -> List[Dict[str, Any]]:
        """List all accessible databases."""
        return self.search(filter_type="database")
    
    def get_database(self, database_id: str) -> Dict[str, Any]:
        """Retrieve database metadata."""
        return self.client.databases.retrieve(database_id=database_id)
    
    def query_database(
        self,
        database_id: str,
        filter: Optional[Dict[str, Any]] = None,
        sorts: Optional[List[Dict[str, str]]] = None,
        page_size: int = 100
    ) -> List[Dict[str, Any]]:
        """Query a database with optional filters and sorts.
        
        Args:
            database_id: Database ID
            filter: Filter criteria
            sorts: Sort criteria
            page_size: Results per page
            
        Returns:
            List of database pages
        """
        params = {
            "database_id": database_id,
            "page_size": page_size
        }
        
        if filter:
            params["filter"] = filter
        if sorts:
            params["sorts"] = sorts
        
        results = []
        has_more = True
        start_cursor = None
        
        while has_more:
            if start_cursor:
                params["start_cursor"] = start_cursor
            
            response = self.client.databases.query(**params)
            results.extend(response["results"])
            
            has_more = response.get("has_more", False)
            start_cursor = response.get("next_cursor")
        
        return results
    
    def create_database(
        self,
        parent: Union[str, Dict[str, str]],
        title: str,
        properties: Dict[str, Any],
        is_inline: bool = False
    ) -> Dict[str, Any]:
        """Create a new database.
        
        Args:
            parent: Parent page ID or dict
            title: Database title
            properties: Database schema properties
            is_inline: Whether database is inline
            
        Returns:
            Created database object
        """
        if isinstance(parent, str):
            parent = {"page_id": parent}
        
        title_content = [{
            "type": "text",
            "text": {"content": title}
        }]
        
        return self.client.databases.create(
            parent=parent,
            title=title_content,
            properties=properties,
            is_inline=is_inline
        )
    
    def update_database(
        self,
        database_id: str,
        title: Optional[str] = None,
        properties: Optional[Dict[str, Any]] = None,
        archived: Optional[bool] = None
    ) -> Dict[str, Any]:
        """Update a database."""
        params = {}
        
        if title:
            params["title"] = [{
                "type": "text",
                "text": {"content": title}
            }]
        if properties:
            params["properties"] = properties
        if archived is not None:
            params["archived"] = archived
        
        return self.client.databases.update(database_id=database_id, **params)
    
    # ===== BLOCK METHODS =====
    
    def get_block_children(
        self,
        block_id: str,
        page_size: int = 100
    ) -> List[Dict[str, Any]]:
        """Get children of a block."""
        results = []
        has_more = True
        start_cursor = None
        
        while has_more:
            params = {"block_id": block_id, "page_size": page_size}
            if start_cursor:
                params["start_cursor"] = start_cursor
            
            response = self.client.blocks.children.list(**params)
            results.extend(response["results"])
            
            has_more = response.get("has_more", False)
            start_cursor = response.get("next_cursor")
        
        return results
    
    def append_blocks(
        self,
        block_id: str,
        children: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Append blocks to a parent block."""
        return self.client.blocks.children.append(
            block_id=block_id,
            children=children
        )
    
    def update_block(
        self,
        block_id: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Update a block."""
        return self.client.blocks.update(block_id=block_id, **kwargs)
    
    def delete_block(self, block_id: str) -> Dict[str, Any]:
        """Delete a block."""
        return self.client.blocks.delete(block_id=block_id)
    
    # ===== USERS METHODS =====
    
    def get_user(self, user_id: str) -> Dict[str, Any]:
        """Get user information."""
        return self.client.users.retrieve(user_id=user_id)
    
    def list_users(self) -> List[Dict[str, Any]]:
        """List all users in the workspace."""
        results = []
        has_more = True
        start_cursor = None
        
        while has_more:
            params = {}
            if start_cursor:
                params["start_cursor"] = start_cursor
            
            response = self.client.users.list(**params)
            results.extend(response["results"])
            
            has_more = response.get("has_more", False)
            start_cursor = response.get("next_cursor")
        
        return results
    
    def get_self(self) -> Dict[str, Any]:
        """Get information about the bot user."""
        return self.client.users.me()
    
    # ===== COMMENTS METHODS =====
    
    def get_comments(self, block_id: str) -> List[Dict[str, Any]]:
        """Get comments on a block."""
        results = []
        has_more = True
        start_cursor = None
        
        while has_more:
            params = {"block_id": block_id}
            if start_cursor:
                params["start_cursor"] = start_cursor
            
            response = self.client.comments.list(**params)
            results.extend(response["results"])
            
            has_more = response.get("has_more", False)
            start_cursor = response.get("next_cursor")
        
        return results
    
    def create_comment(
        self,
        parent: Union[str, Dict[str, str]],
        rich_text: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Create a comment."""
        if isinstance(parent, str):
            parent = {"page_id": parent}
        
        return self.client.comments.create(
            parent=parent,
            rich_text=rich_text
        )