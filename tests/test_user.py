"""Tests for user management commands."""
import json
from unittest.mock import Mock, patch
import pytest
from click.testing import CliRunner

from notion_cli.commands.user import user


class TestUserCommands:
    """Test user command operations."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
        self.mock_users = [
            {
                'id': 'user-123',
                'object': 'user',
                'type': 'person',
                'name': 'John Doe',
                'person': {
                    'email': 'john.doe@example.com'
                },
                'avatar_url': None
            },
            {
                'id': 'user-456',
                'object': 'user',
                'type': 'person',
                'name': 'Jane Smith',
                'person': {
                    'email': 'jane.smith@example.com'
                },
                'avatar_url': 'https://example.com/avatar.jpg'
            },
            {
                'id': 'bot-789',
                'object': 'user',
                'type': 'bot',
                'name': 'Test Bot',
                'bot': {
                    'owner': {
                        'type': 'workspace',
                        'workspace': True
                    },
                    'workspace_name': 'Test Workspace'
                },
                'avatar_url': None
            }
        ]
        
        self.mock_bot_user = {
            'id': 'bot-integration',
            'object': 'user',
            'type': 'bot',
            'name': 'Notion CLI Integration',
            'bot': {
                'owner': {
                    'type': 'workspace',
                    'workspace': True
                },
                'workspace_name': 'My Workspace'
            }
        }
    
    @patch('notion_cli.commands.user.NotionClient')
    def test_list_users_table_output(self, mock_client_class):
        """Test listing users with table output."""
        mock_client = mock_client_class.return_value
        mock_client.list_users.return_value = self.mock_users
        
        result = self.runner.invoke(user, ['list'])
        
        assert result.exit_code == 0
        assert 'Workspace Users (3 total)' in result.output
        assert 'John Doe' in result.output
        assert 'Jane Smith' in result.output
        assert 'Test Bot' in result.output
        assert 'john.doe@example.com' in result.output
        mock_client.list_users.assert_called_once()
    
    @patch('notion_cli.commands.user.NotionClient')
    def test_list_users_json_output(self, mock_client_class):
        """Test listing users with JSON output."""
        mock_client = mock_client_class.return_value
        mock_client.list_users.return_value = self.mock_users
        
        result = self.runner.invoke(user, ['list', '--output', 'json'])
        
        assert result.exit_code == 0
        output_data = json.loads(result.output)
        assert len(output_data) == 3
        assert output_data[0]['name'] == 'John Doe'
        assert output_data[1]['person']['email'] == 'jane.smith@example.com'
        assert output_data[2]['type'] == 'bot'
    
    @patch('notion_cli.commands.user.NotionClient')
    def test_list_users_with_limit(self, mock_client_class):
        """Test listing users with limit."""
        mock_client = mock_client_class.return_value
        mock_client.list_users.return_value = self.mock_users
        
        result = self.runner.invoke(user, ['list', '--limit', '2', '--output', 'json'])
        
        assert result.exit_code == 0
        output_data = json.loads(result.output)
        assert len(output_data) == 2
    
    @patch('notion_cli.commands.user.NotionClient')
    def test_get_user(self, mock_client_class):
        """Test getting a specific user."""
        mock_client = mock_client_class.return_value
        mock_client.get_user.return_value = self.mock_users[0]
        
        result = self.runner.invoke(user, ['get', 'user-123'])
        
        assert result.exit_code == 0
        output_data = json.loads(result.output)
        assert output_data['name'] == 'John Doe'
        assert output_data['person']['email'] == 'john.doe@example.com'
        mock_client.get_user.assert_called_once_with('user-123')
    
    @patch('notion_cli.commands.user.NotionClient')
    def test_get_user_table_output(self, mock_client_class):
        """Test getting a user with table output."""
        mock_client = mock_client_class.return_value
        mock_client.get_user.return_value = self.mock_users[1]
        
        result = self.runner.invoke(user, ['get', 'user-456', '--output', 'table'])
        
        assert result.exit_code == 0
        assert 'User Details' in result.output
        assert 'Jane Smith' in result.output
        assert 'jane.smith@example.com' in result.output
        assert 'https://example.com/avatar.jpg' in result.output
    
    @patch('notion_cli.commands.user.NotionClient')
    def test_get_me(self, mock_client_class):
        """Test getting current integration user."""
        mock_client = mock_client_class.return_value
        mock_client.get_self.return_value = self.mock_bot_user
        
        result = self.runner.invoke(user, ['me'])
        
        assert result.exit_code == 0
        output_data = json.loads(result.output)
        assert output_data['name'] == 'Notion CLI Integration'
        assert output_data['type'] == 'bot'
        assert output_data['bot']['workspace_name'] == 'My Workspace'
        mock_client.get_self.assert_called_once()
    
    @patch('notion_cli.commands.user.NotionClient')
    def test_get_me_table_output(self, mock_client_class):
        """Test getting current user with table output."""
        mock_client = mock_client_class.return_value
        mock_client.get_self.return_value = self.mock_bot_user
        
        result = self.runner.invoke(user, ['me', '--output', 'table'])
        
        assert result.exit_code == 0
        assert 'Current Integration User' in result.output
        assert 'Notion CLI Integration' in result.output
        assert 'Integration' in result.output
        assert 'My Workspace' in result.output
    
    @patch('notion_cli.commands.user.NotionClient')
    def test_search_users(self, mock_client_class):
        """Test searching for users."""
        mock_client = mock_client_class.return_value
        mock_client.list_users.return_value = self.mock_users
        
        result = self.runner.invoke(user, ['search', 'jane'])
        
        assert result.exit_code == 0
        assert 'Jane Smith' in result.output
        assert 'jane.smith@example.com' in result.output
        assert 'John Doe' not in result.output
    
    @patch('notion_cli.commands.user.NotionClient')
    def test_search_users_by_email(self, mock_client_class):
        """Test searching users by email."""
        mock_client = mock_client_class.return_value
        mock_client.list_users.return_value = self.mock_users
        
        result = self.runner.invoke(user, ['search', 'john.doe@example.com', '--output', 'json'])
        
        assert result.exit_code == 0
        output_data = json.loads(result.output)
        assert len(output_data) == 1
        assert output_data[0]['name'] == 'John Doe'
    
    @patch('notion_cli.commands.user.NotionClient')
    def test_search_users_no_results(self, mock_client_class):
        """Test searching with no results."""
        mock_client = mock_client_class.return_value
        mock_client.list_users.return_value = self.mock_users
        
        result = self.runner.invoke(user, ['search', 'nonexistent'])
        
        assert result.exit_code == 0
        assert "No users found matching 'nonexistent'" in result.output
    
    @patch('notion_cli.commands.user.NotionClient')
    def test_list_users_empty(self, mock_client_class):
        """Test listing users when none exist."""
        mock_client = mock_client_class.return_value
        mock_client.list_users.return_value = []
        
        result = self.runner.invoke(user, ['list'])
        
        assert result.exit_code == 0
        assert 'No users found in workspace' in result.output
    
    @patch('notion_cli.commands.user.NotionClient')
    def test_user_command_error_handling(self, mock_client_class):
        """Test error handling in user commands."""
        mock_client = mock_client_class.return_value
        mock_client.get_user.side_effect = Exception("API Error")
        
        result = self.runner.invoke(user, ['get', 'invalid-id'])
        
        assert result.exit_code != 0
        assert 'Failed to get user: API Error' in result.output
    
    def test_user_help(self):
        """Test user command help."""
        result = self.runner.invoke(user, ['--help'])
        
        assert result.exit_code == 0
        assert 'Manage Notion workspace users' in result.output
        assert 'list' in result.output
        assert 'get' in result.output
        assert 'me' in result.output
        assert 'search' in result.output