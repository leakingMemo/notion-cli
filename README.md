# Notion CLI

A powerful command-line interface for interacting with Notion. Manage pages, databases, and content directly from your terminal.

## Features

- 🚀 **Full CRUD Operations** - Create, read, update, and delete pages and databases
- 🔍 **Advanced Search** - Search across your entire workspace with filters
- 📊 **Database Queries** - Query databases with complex filters and sorting
- 📝 **Rich Content Support** - Handle all Notion content types including rich text
- 🎨 **Multiple Output Formats** - JSON, YAML, table, or plain text output
- ⚡ **Fast & Efficient** - Optimized for performance with async operations
- 🔧 **Configurable** - Use config files or environment variables
- 🌈 **Interactive Mode** - User-friendly prompts for complex operations

## Installation

### From PyPI (recommended)

```bash
pip install notion-cli
```

### From Source

```bash
git clone https://github.com/leakingMemo/notion-cli.git
cd notion-cli
pip install -e .
```

## Quick Start

### 1. Set up your Notion API key

```bash
# Set via environment variable
export NOTION_API_KEY="your-api-key-here"

# Or create a config file
notion-cli config init
```

### 2. Basic Commands

```bash
# Search for pages
notion-cli search "meeting notes"

# List all databases
notion-cli database list

# Query a database
notion-cli database query <database-id> --filter "Status=Done"

# Create a new page
notion-cli page create --title "My New Page" --parent <parent-id>

# Export a page
notion-cli page export <page-id> --format markdown
```

## Configuration

### Environment Variables

- `NOTION_API_KEY` - Your Notion integration API key (required)
- `NOTION_DEFAULT_DATABASE` - Default database ID for operations
- `NOTION_OUTPUT_FORMAT` - Default output format (json|yaml|table|text)

### Config File

Create `~/.notion-cli/config.yaml`:

```yaml
api_key: your-api-key-here
default_database: your-database-id
output_format: table
color_output: true
```

## Usage Examples

### Pages

```bash
# Create a page
notion-cli page create --title "Project Plan" --parent workspace

# Read a page
notion-cli page get <page-id>

# Update a page
notion-cli page update <page-id> --title "Updated Title"

# Delete (archive) a page
notion-cli page delete <page-id>

# Search pages
notion-cli page search "quarterly report"
```

### Databases

```bash
# List all databases
notion-cli database list

# Query with filters
notion-cli database query <db-id> \
  --filter "Status=In Progress" \
  --filter "Priority=High" \
  --sort "Due Date:ascending"

# Create a database entry
notion-cli database create-page <db-id> \
  --property "Name=New Task" \
  --property "Status=To Do" \
  --property "Due Date=2024-12-31"

# Export database to CSV
notion-cli database export <db-id> --format csv > tasks.csv
```

### Blocks

```bash
# Get page content blocks
notion-cli block children <page-id>

# Append content to a page
notion-cli block append <page-id> --text "New paragraph"

# Create complex content
notion-cli block append <page-id> \
  --heading "Section Title" \
  --text "Paragraph text" \
  --bullet "First item" \
  --bullet "Second item"
```

### Interactive Mode

```bash
# Start interactive mode
notion-cli interactive

# Use the interactive prompt
> search my notes
> database query <tab-complete-id>
> help
```

## Output Formats

Control output format with `--output` or `-o`:

```bash
# JSON output (default)
notion-cli page get <page-id> -o json

# YAML output
notion-cli page get <page-id> -o yaml

# Table output (great for databases)
notion-cli database query <db-id> -o table

# Plain text (simplified)
notion-cli page get <page-id> -o text
```

## Advanced Features

### Bulk Operations

```bash
# Create multiple pages from CSV
notion-cli bulk create-pages data.csv --parent-id <parent-id>

# Create pages from JSON with custom title field
notion-cli bulk create-pages pages.json --parent-id <parent-id> --format json --title-field name

# Preview bulk creation (dry run)
notion-cli bulk create-pages data.csv --parent-id <parent-id> --dry-run

# Update multiple pages from CSV
notion-cli bulk update-pages updates.csv --id-field page_id

# Delete multiple pages
notion-cli bulk delete-pages page-ids.csv --force

# List pages for bulk operations
notion-cli bulk list-pages --database-id <db-id> --export-file pages.csv
```

Example CSV format for creating pages:
```csv
title,content,status,priority
"Q1 Planning","Quarterly planning meeting notes","Published","High"
"Product Roadmap","Feature planning for next release","Draft","Medium"
```

Example CSV format for updating pages:
```csv
id,status,priority
"page-id-1","Completed","Low"
"page-id-2","In Review","High"
```

### Templates

```bash
# Save a page as template
notion-cli template save <page-id> --name "meeting-notes"

# Create from template
notion-cli template use "meeting-notes" --title "Team Standup 2024-01-15"
```

### Integrations

```bash
# Export to other formats
notion-cli export <page-id> --format markdown > page.md
notion-cli export <database-id> --format csv > data.csv

# Import from files
notion-cli import notes.md --parent <parent-id>
```

## Development

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/leakingMemo/notion-cli.git
cd notion-cli

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=notion_cli

# Run specific test file
pytest tests/test_pages.py
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with [notion-client](https://github.com/ramnes/notion-sdk-py)
- Inspired by the official Notion API

## Support

- 📫 Report issues on [GitHub Issues](https://github.com/leakingMemo/notion-cli/issues)
- 💬 Join discussions on [GitHub Discussions](https://github.com/leakingMemo/notion-cli/discussions)
- 📖 Read the [documentation](https://github.com/leakingMemo/notion-cli/wiki)