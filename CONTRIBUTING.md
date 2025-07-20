# Contributing to Notion CLI

Thank you for considering contributing to Notion CLI! This document provides guidelines and instructions for contributing.

## Code of Conduct

By participating in this project, you agree to abide by our Code of Conduct:
- Be respectful and inclusive
- Welcome newcomers and help them get started
- Focus on constructive criticism
- Respect differing viewpoints and experiences

## How to Contribute

### Reporting Issues

1. Check if the issue already exists in the [issue tracker](https://github.com/leakingMemo/notion-cli/issues)
2. If not, create a new issue with:
   - Clear, descriptive title
   - Detailed description of the problem
   - Steps to reproduce
   - Expected vs actual behavior
   - System information (OS, Python version)

### Suggesting Features

1. Check existing issues and discussions
2. Open a new issue with the "feature request" label
3. Describe the feature and its use case
4. Explain why it would be valuable

### Contributing Code

#### Setup Development Environment

```bash
# Fork and clone the repository
git clone https://github.com/YOUR_USERNAME/notion-cli.git
cd notion-cli

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

#### Development Workflow

1. Create a feature branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes following our coding standards

3. Write or update tests:
   ```bash
   pytest tests/
   ```

4. Run linting and formatting:
   ```bash
   black notion_cli tests
   flake8 notion_cli tests
   mypy notion_cli
   ```

5. Commit your changes:
   ```bash
   git add .
   git commit -m "feat: add new feature"
   ```

6. Push to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```

7. Create a Pull Request

### Coding Standards

#### Python Style

- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/)
- Use [Black](https://github.com/psf/black) for formatting
- Use type hints where appropriate
- Maximum line length: 100 characters

#### Commit Messages

Follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `style:` Code style changes (formatting, etc.)
- `refactor:` Code refactoring
- `test:` Test changes
- `chore:` Build process or auxiliary tool changes

Examples:
```
feat: add database export to Excel format
fix: handle empty search results gracefully
docs: update installation instructions
```

#### Code Structure

- Keep functions small and focused
- Use descriptive variable and function names
- Add docstrings to all public functions and classes
- Handle errors gracefully with helpful messages

### Testing

#### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=notion_cli

# Run specific test file
pytest tests/test_client.py

# Run tests matching pattern
pytest -k "test_search"
```

#### Writing Tests

- Write tests for all new functionality
- Aim for high test coverage (>80%)
- Use fixtures for common test data
- Mock external API calls
- Test both success and error cases

Example test:
```python
def test_search_with_query(mock_notion_client):
    """Test search with a query string."""
    mock_notion_client.search.return_value = [
        {"id": "1", "title": "Test Page"}
    ]
    
    results = mock_notion_client.search(query="test")
    
    assert len(results) == 1
    assert results[0]["title"] == "Test Page"
    mock_notion_client.search.assert_called_once_with(query="test")
```

### Documentation

#### Docstring Format

Use Google-style docstrings:

```python
def search(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Search for pages and databases.
    
    Args:
        query: Search query string
        limit: Maximum number of results
        
    Returns:
        List of search results
        
    Raises:
        NotionAPIError: If the API request fails
    """
```

#### Updating Documentation

- Update README.md for user-facing changes
- Update docstrings for API changes
- Add examples for new features
- Keep the CLI help text up to date

### Pull Request Process

1. **Before submitting:**
   - Ensure all tests pass
   - Update documentation
   - Add yourself to CONTRIBUTORS.md (if first contribution)

2. **PR Description:**
   - Reference related issues
   - Describe what changes were made
   - Include screenshots for UI changes
   - List any breaking changes

3. **Review Process:**
   - PRs require at least one review
   - Address reviewer feedback
   - Keep PR focused on a single feature/fix

4. **After Merge:**
   - Delete your feature branch
   - Pull the latest main branch

## Release Process

1. Update version in `setup.py` and `pyproject.toml`
2. Update CHANGELOG.md
3. Create a release PR
4. After merge, tag the release:
   ```bash
   git tag -a v1.2.3 -m "Release version 1.2.3"
   git push origin v1.2.3
   ```
5. GitHub Actions will automatically publish to PyPI

## Getting Help

- Join our [GitHub Discussions](https://github.com/leakingMemo/notion-cli/discussions)
- Check the [Wiki](https://github.com/leakingMemo/notion-cli/wiki)
- Ask questions in issues with the "question" label

## Recognition

Contributors will be:
- Listed in CONTRIBUTORS.md
- Mentioned in release notes
- Given credit in the project README

Thank you for contributing to Notion CLI! 🎉