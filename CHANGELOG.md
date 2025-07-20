# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial release of Notion CLI
- Full CRUD operations for pages, databases, and blocks
- Search functionality across Notion workspace
- Multiple output formats (JSON, YAML, table, text)
- Interactive mode with command completion
- Configuration management with file and environment variable support
- Database querying with filters and sorting
- Page and database export functionality
- Bulk operations support
- Rich formatted output with color support
- Command history in interactive mode
- Comprehensive test suite
- Full documentation and examples

### Security
- API keys are masked in configuration display
- Secure storage of credentials in config files

## [0.1.0] - 2024-01-20

### Added
- Initial project structure
- Core Notion API client wrapper
- Basic CLI commands
- Configuration system
- Output formatters
- Test framework

[Unreleased]: https://github.com/leakingMemo/notion-cli/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/leakingMemo/notion-cli/releases/tag/v0.1.0