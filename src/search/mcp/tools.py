# tools.py
"""
This file contains the tools for the Search MCP service.
"""

from mcp.types import Tool

def get_search_tools() -> list[Tool]:
    """
    Get the tools for the Search server.
    """
    return [
        Tool(
            name="search_index_list",
            description="List all search indexes in the account",
            inputSchema={
                "type": "object",
                "properties": {
                    "service_name": {
                        "type": "string",
                        "description": "Name of the search account",
                    },
                },
                "required": ["service_name"],
            },
        ),
        Tool(
            name="search_index_delete",
            description="Delete a search index",
            inputSchema={
                "type": "object",
                "properties": {
                    "service_name": {
                        "type": "string",
                        "description": "Name of the search account",
                    },
                    "index_name": {
                        "type": "string",
                        "description": "Name of the search index",
                    },
                },
                "required": ["service_name", "index_name"],
            },
        ),
        Tool(
            name="search_index_describe",
            description="Describe a search index",
            inputSchema={
                "type": "object",
                "properties": {
                    "service_name": {
                        "type": "string",
                        "description": "Name of the search account",
                    },
                    "index_name": {
                        "type": "string",
                        "description": "Name of the search index",
                    },
                },
                "required": ["service_name", "index_name"],
            },
        ),
        Tool(
            name="search_index_query",
            description="Query a search index",
            inputSchema={
                "type": "object",
                "properties": {
                    "service_name": {
                        "type": "string",
                        "description": "Name of the search account",
                    },
                    "index_name": {
                        "type": "string",
                        "description": "Name of the search index",
                    },
                    "query": {
                        "type": "string",
                        "description": "Query to execute",
                    },
                },
                "required": ["service_name", "index_name", "query"],
            },
        )
    ]