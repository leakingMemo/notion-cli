#!/usr/bin/env python3
"""Quick start example for Notion CLI."""

import os
from notion_cli import NotionClient

# Initialize client
client = NotionClient()

# Search for content
print("🔍 Searching for pages...")
results = client.search("meeting notes", filter_type="page", page_size=5)

for page in results:
    # Extract title
    title = "Untitled"
    for prop in page.get("properties", {}).values():
        if prop.get("type") == "title":
            title_arr = prop.get("title", [])
            if title_arr:
                title = title_arr[0].get("plain_text", "Untitled")
            break
    
    print(f"📄 {title}")
    print(f"   ID: {page['id']}")
    print(f"   URL: {page['url']}")
    print()

# List databases
print("\n📊 Available databases:")
databases = client.list_databases()

for db in databases[:5]:
    db_title = "Untitled"
    if db.get("title"):
        db_title = "".join([t.get("plain_text", "") for t in db["title"]])
    
    print(f"🗄️  {db_title}")
    print(f"   ID: {db['id']}")
    print()

print("\n✅ Quick start complete!")
print("Run 'notion-cli --help' for more commands")