"""Tests for bulk operations."""
import json
import csv
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pytest
from click.testing import CliRunner

from notion_cli.commands.bulk import bulk, load_data_from_file


class TestBulkOperations:
    """Test bulk command operations."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
        self.mock_client = Mock()
    
    def test_load_csv_data(self):
        """Test loading data from CSV file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            writer = csv.DictWriter(f, fieldnames=['title', 'content', 'status'])
            writer.writeheader()
            writer.writerow({'title': 'Page 1', 'content': 'Content 1', 'status': 'Published'})
            writer.writerow({'title': 'Page 2', 'content': 'Content 2', 'status': 'Draft'})
            f.flush()
            
            data = load_data_from_file(f.name, 'csv')
            
        assert len(data) == 2
        assert data[0]['title'] == 'Page 1'
        assert data[1]['status'] == 'Draft'
        
        Path(f.name).unlink()
    
    def test_load_json_data(self):
        """Test loading data from JSON file."""
        test_data = [
            {'title': 'Page 1', 'content': 'Content 1'},
            {'title': 'Page 2', 'content': 'Content 2'}
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_data, f)
            f.flush()
            
            data = load_data_from_file(f.name, 'json')
            
        assert len(data) == 2
        assert data[0]['title'] == 'Page 1'
        
        Path(f.name).unlink()
    
    @patch('notion_cli.commands.bulk.NotionClient')
    def test_create_pages_dry_run(self, mock_client_class):
        """Test create-pages command in dry run mode."""
        # Create test CSV file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            writer = csv.DictWriter(f, fieldnames=['title', 'content'])
            writer.writeheader()
            writer.writerow({'title': 'Test Page 1', 'content': 'Content 1'})
            writer.writerow({'title': 'Test Page 2', 'content': 'Content 2'})
            f.flush()
            
            result = self.runner.invoke(bulk, [
                'create-pages', f.name,
                '--parent-id', 'parent-123',
                '--dry-run'
            ])
            
        assert result.exit_code == 0
        assert 'DRY RUN MODE' in result.output
        assert 'Test Page 1' in result.output
        assert 'Test Page 2' in result.output
        
        # Client should not be called in dry run
        mock_client_class.return_value.create_page.assert_not_called()
        
        Path(f.name).unlink()
    
    @patch('notion_cli.commands.bulk.NotionClient')
    @patch('notion_cli.commands.bulk.Confirm.ask')
    def test_create_pages_execution(self, mock_confirm, mock_client_class):
        """Test create-pages command execution."""
        mock_confirm.return_value = True
        mock_client = mock_client_class.return_value
        mock_client.create_page.return_value = {
            'id': 'page-123',
            'url': 'https://notion.so/page-123'
        }
        
        # Create test CSV file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            writer = csv.DictWriter(f, fieldnames=['title', 'content'])
            writer.writeheader()
            writer.writerow({'title': 'Test Page', 'content': 'Test Content'})
            f.flush()
            
            result = self.runner.invoke(bulk, [
                'create-pages', f.name,
                '--parent-id', 'parent-123'
            ])
            
        assert result.exit_code == 0
        assert 'Successfully created 1 pages' in result.output
        mock_client.create_page.assert_called_once()
        
        Path(f.name).unlink()
    
    @patch('notion_cli.commands.bulk.NotionClient')
    def test_update_pages_missing_id_field(self, mock_client_class):
        """Test update-pages with missing ID field."""
        # Create test CSV without ID field
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            writer = csv.DictWriter(f, fieldnames=['title', 'content'])
            writer.writeheader()
            writer.writerow({'title': 'Test Page', 'content': 'Content'})
            f.flush()
            
            result = self.runner.invoke(bulk, [
                'update-pages', f.name
            ])
            
        assert result.exit_code != 0
        assert "items missing 'id' field" in result.output
        
        Path(f.name).unlink()
    
    @patch('notion_cli.commands.bulk.NotionClient')
    @patch('notion_cli.commands.bulk.Confirm.ask')
    def test_delete_pages_execution(self, mock_confirm, mock_client_class):
        """Test delete-pages command execution."""
        mock_confirm.return_value = True
        mock_client = mock_client_class.return_value
        
        # Create test CSV with page IDs
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            writer = csv.DictWriter(f, fieldnames=['id', 'reason'])
            writer.writeheader()
            writer.writerow({'id': 'page-123', 'reason': 'Obsolete'})
            writer.writerow({'id': 'page-456', 'reason': 'Duplicate'})
            f.flush()
            
            result = self.runner.invoke(bulk, [
                'delete-pages', f.name
            ])
            
        assert result.exit_code == 0
        assert 'Successfully archived 2 pages' in result.output
        assert mock_client.update_page.call_count == 2
        
        Path(f.name).unlink()
    
    @patch('notion_cli.commands.bulk.NotionClient')
    def test_list_pages_from_database(self, mock_client_class):
        """Test list-pages from database."""
        mock_client = mock_client_class.return_value
        mock_client.query_database.return_value = {
            'results': [
                {
                    'id': 'page-123',
                    'properties': {
                        'title': {
                            'title': [{'plain_text': 'Page 1'}]
                        }
                    },
                    'created_time': '2024-01-01T00:00:00Z',
                    'url': 'https://notion.so/page-123'
                }
            ]
        }
        
        result = self.runner.invoke(bulk, [
            'list-pages',
            '--database-id', 'db-123',
            '--output', 'json'
        ])
        
        assert result.exit_code == 0
        output = json.loads(result.output)
        assert len(output) == 1
        assert output[0]['id'] == 'page-123'
        assert output[0]['title'] == 'Page 1'
    
    def test_bulk_help(self):
        """Test bulk command help."""
        result = self.runner.invoke(bulk, ['--help'])
        assert result.exit_code == 0
        assert 'Perform bulk operations' in result.output
        assert 'create-pages' in result.output
        assert 'update-pages' in result.output
        assert 'delete-pages' in result.output