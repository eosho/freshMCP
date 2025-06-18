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
            name="search_index_create",
            description="Create a search index with fields for id, content, and metadata",
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
            description="Describe a search index including its fields and configuration",
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
            description="Query a search index with support for different query types (simple, full, semantic)",
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
                    "query_type": {
                        "type": "string",
                        "description": "Type of query to execute (simple, full, or semantic)",
                        "enum": ["simple", "full", "semantic"],
                        "default": "simple"
                    }
                },
                "required": ["service_name", "index_name", "query"],
            },
        )
    ]