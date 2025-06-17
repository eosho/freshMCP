# tools.py
"""
This file contains the tools for the Cosmos DB MCP service.
"""

from mcp.types import Tool

def get_cosmosdb_tools() -> list[Tool]:
    return [
        Tool(
            name="cosmosdb_database_list",
            description="List all Cosmos DB databases in an account",
            inputSchema={
                "type": "object",
                "properties": {
                    "account_name": {
                        "type": "string",
                        "description": "Name of the Cosmos DB account",
                    },
                },
                "required": ["account_name"],
            },
        ),
        Tool(
            name="cosmosdb_database_describe",
            description="Describe a Cosmos DB database",
            inputSchema={
                "type": "object",
                "properties": {
                    "account_name": {
                        "type": "string",
                        "description": "Name of the Cosmos DB account",
                    },
                    "database_name": {
                        "type": "string",
                        "description": "Name of the Cosmos DB database",
                    },
                },
                "required": ["account_name", "database_name"],
            },
        ),
        Tool(
            name="cosmosdb_database_create",
            description="Create a new Cosmos DB database",
            inputSchema={
                "type": "object",
                "properties": {
                    "account_name": {
                        "type": "string",
                        "description": "Name of the Cosmos DB account",
                    },
                    "database_name": {
                        "type": "string",
                        "description": "Name of the Cosmos DB database",
                    },
                },
                "required": ["account_name", "database_name"],
            },
        ),
        Tool(
            name="cosmosdb_container_create",
            description="Create a new Cosmos DB container",
            inputSchema={
                "type": "object",
                "properties": {
                    "account_name": {
                        "type": "string",
                        "description": "Name of the Cosmos DB account",
                    },
                    "container_name": {
                        "type": "string",
                        "description": "Name of the Cosmos DB container",
                    },
                    "database_name": {
                        "type": "string",
                        "description": "Name of the Cosmos DB database.",
                    },
                    "partition_key": {
                        "type": "object",
                        "description": "Partition key definition for the container (e.g., {'paths': ['/partitionKey'], 'kind': 'Hash'})",
                    },
                },
                "required": [
                    "account_name",
                    "container_name",
                    "partition_key"
                ],
            },
        ),
        Tool(
            name="cosmosdb_container_list",
            description="List all Cosmos DB containers in a database",
            inputSchema={
                "type": "object",
                "properties": {
                    "account_name": {
                        "type": "string",
                        "description": "Name of the Cosmos DB account",
                    },
                    "database_name": {
                        "type": "string",
                        "description": "Name of the Cosmos DB database",
                    }
                },
                "required": [
                  "account_name",
                  "database_name"
                ],
            },
        ),
        Tool(
            name="cosmosdb_container_delete",
            description="Delete a Cosmos DB container",
            inputSchema={
                "type": "object",
                "properties": {
                    "account_name": {
                        "type": "string",
                        "description": "Name of the Cosmos DB account",
                    },
                    "container_name": {
                        "type": "string",
                        "description": "Name of the Cosmos DB container",
                    },
                    "database_name": {
                        "type": "string",
                        "description": "Name of the Cosmos DB database",
                    },
                },
                "required": [
                  "account_name",
                  "container_name",
                  "database_name"
                ],
            },
        ),
        Tool(
            name="cosmosdb_item_read",
            description="Read an item from a Cosmos DB container",
            inputSchema={
                "type": "object",
                "properties": {
                    "account_name": {
                        "type": "string",
                        "description": "Name of the Cosmos DB account",
                    },
                    "container_name": {
                        "type": "string",
                        "description": "Name of the Cosmos DB container",
                    },
                    "database_name": {
                        "type": "string",
                        "description": "Name of the Cosmos DB database.",
                    },
                    "item_id": {
                        "type": "string",
                        "description": "ID of the item to read",
                    },
                    "partition_key": {
                        "type": "string",
                        "description": "Partition key value for the item",
                    },
                },
                "required": [
                  "account_name",
                  "container_name",
                  "database_name",
                  "item_id",
                  "partition_key"
                ],
            },
        ),
        Tool(
            name="cosmosdb_item_query",
            description="Query items in a Cosmos DB container using SQL",
            inputSchema={
                "type": "object",
                "properties": {
                    "account_name": {
                        "type": "string",
                        "description": "Name of the Cosmos DB account",
                    },
                    "container_name": {
                        "type": "string",
                        "description": "Name of the Cosmos DB container",
                    },
                    "database_name": {
                        "type": "string",
                        "description": "Name of the Cosmos DB database",
                    },
                    "query": {
                        "type": "string",
                        "description": "Cosmos DB SQL query string",
                    },
                    "parameters": {
                        "type": "array",
                        "description": "Parameters for the SQL query (optional)",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "value": {}
                            },
                        },
                    },
                },
                "required": [
                  "account_name",
                  "container_name",
                  "database_name",
                  "query"
                ],
            },
        ),
    ]