"""Notion CLI - A powerful command-line interface for Notion."""

__version__ = "0.1.0"
__author__ = "Nathan D'Souza"
__email__ = "nathan@example.com"

from .client import NotionClient
from .config import Config

__all__ = ["NotionClient", "Config", "__version__"]