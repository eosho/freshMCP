# server.py

"""
This file contains the server for the Cosmos DB MCP service.
"""

import logging
import sys
from typing import List, Dict, Any
import uvicorn
import argparse
from mcp.server.fastmcp import FastMCP
from .cosmos import CosmosDBServer
from mcp.server import Server
from starlette.applications import Starlette
from mcp.server.sse import SseServerTransport
from starlette.requests import Request
from starlette.routing import Mount, Route
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

# Global cosmos service instance
cosmos_service = CosmosDBServer()

# Initialize MCP server
mcp = FastMCP("cosmosdb_mcp")

# Version information
VERSION = "1.0.0"

# Static resource
@mcp.resource("config://version")
def get_version() -> str:
    """
    Get the version of the server.
    Returns:
        str: The server version
    """
    logger.info("Version requested")
    return VERSION

# Register basic resources and tools
@mcp.resource("echo://{message}")
def echo_resource(message: str) -> str:
    """
    Echo the message.
    Args:
        message (str): The message to echo
    Returns:
        str: The echoed message
    """
    logger.info(f"Echo resource called with message: {message}")
    return f"Resource echo: {message}"

# Register the echo tool
@mcp.tool(
    name="echo",
    description="Echo the message"
)
async def echo_tool(message: str) -> str:
    """
    Echo the message.
    Args:
        message (str): The message to process
    Returns:
        str: The processed message
    """
    logger.info(f"Echo tool called with message: {message}")
    return f"Tool echo: {message}"

@mcp.prompt(
    name="prompt",
    description="Prompt the message"
)
async def prompt_resource(message: str) -> str:
    """
    Prompt the message.
    Args:
        message (str): The message to process
    Returns:
        str: The processed message
    """
    logger.info(f"Prompt resource called with message: {message}")
    return f"Please process this message: {message}"

@mcp.tool(
    name="list_databases",
    description="List the databases in the account"
)
async def list_databases(account_name: str) -> List[str]:
    """
    List the databases in the account.
    Args:
        account_name (str): The name of the account
    Returns:
        List[str]: A list of the databases
    """
    return await cosmos_service._list_databases(account_name)

@mcp.tool(
    name="describe_database",
    description="Describe the database including its properties and settings"
)
async def describe_database(account_name: str, database_name: str) -> Dict[str, Any]:
    """
    Describe the database.
    Args:
        account_name (str): The name of the account
        database_name (str): The name of the database
    Returns:
        Dict[str, Any]: A dictionary containing the database details
    """
    return await cosmos_service._describe_database(account_name, database_name)

@mcp.tool(
    name="list_containers",
    description="List the containers in the database"
)
async def list_containers(account_name: str, database_name: str) -> List[str]:
    """
    List the containers in the database.
    Args:
        account_name (str): The name of the account
        database_name (str): The name of the database
    Returns:
        List[str]: A list of the containers
    """
    return await cosmos_service._list_containers(account_name, database_name)

@mcp.tool(
    name="create_container",
    description="Create a container in the database with specified partition key"
)
async def create_container(account_name: str, database_name: str, container_name: str, partition_key: str) -> Dict[str, Any]:
    """
    Create a container in the database.
    Args:
        account_name (str): The name of the account
        database_name (str): The name of the database
        container_name (str): The name of the container
        partition_key (str): The partition key of the container
    Returns:
        Dict[str, Any]: A dictionary containing the container details
    """
    return await cosmos_service._create_container(account_name, database_name, container_name, partition_key)

@mcp.tool(
    name="delete_container",
    description="Delete a container from the database"
)
async def delete_container(account_name: str, database_name: str, container_name: str) -> Dict[str, Any]:
    """
    Delete a container in the database.
    Args:
        account_name (str): The name of the account
        database_name (str): The name of the database
        container_name (str): The name of the container
    Returns:
        Dict[str, Any]: A dictionary containing the operation result
    """
    return await cosmos_service._delete_container(account_name, database_name, container_name)

@mcp.tool(
    name="read_item",
    description="Read an item from the container using its ID and partition key"
)
async def read_item(account_name: str, database_name: str, container_name: str, item_id: str, partition_key: str) -> Dict[str, Any]:
    """
    Read an item in the container.
    Args:
        account_name (str): The name of the account
        database_name (str): The name of the database
        container_name (str): The name of the container
        item_id (str): The ID of the item
        partition_key (str): The partition key of the item
    Returns:
        Dict[str, Any]: A dictionary containing the item
    """
    return await cosmos_service._read_item(account_name, database_name, container_name, item_id, partition_key)

@mcp.tool(
    name="query_item",
    description="Query items in the container using SQL-like query syntax"
)
async def query_items(account_name: str, database_name: str, container_name: str, query: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Query an item in the container.
    Args:
        account_name (str): The name of the account
        database_name (str): The name of the database
        container_name (str): The name of the container
        query (str): The query to execute
        parameters (Dict[str, Any]): The parameters to pass to the query
    Returns:
        Dict[str, Any]: A dictionary containing the query results
    """
    return await cosmos_service._query_items(account_name, database_name, container_name, query, parameters)

def create_starlette_app(mcp_server: Server, *, debug: bool = False) -> Starlette:
    """Create a Starlette application that can serve the provided mcp server with SSE.
    Args:
        mcp_server (Server): The MCP server to serve
        debug (bool): Whether to run in debug mode
    Returns:
        Starlette: The Starlette application
    """
    sse = SseServerTransport("/cosmos/messages/")

    async def handle_sse(request: Request) -> None:
        """Handle SSE connections.
        Args:
            request (Request): The incoming request
        """
        logger.info("Handling new SSE connection")
        async with sse.connect_sse(
            request.scope,
            request.receive,
            request._send,
        ) as (read_stream, write_stream):
            await mcp_server.run(
                read_stream,
                write_stream,
                mcp_server.create_initialization_options(),
            )

    return Starlette(
        debug=debug,
        routes=[
            Route("/cosmos/sse", endpoint=handle_sse),
            Mount("/cosmos/messages/", app=sse.handle_post_message),
        ],
        middleware=[
            Middleware(
                CORSMiddleware,
                allow_origins=["*"],
                allow_methods=["*"],
                allow_headers=["*"],
            )
        ]
    )

# Initialize server instances
mcp_server = mcp._mcp_server
starlette_app = create_starlette_app(mcp_server, debug=True)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run MCP SSE-based server')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=8001, help='Port to listen on')
    parser.add_argument('--log-level', default='INFO', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                      help='Set the logging level')
    args = parser.parse_args()

    # Configure logging level from command line
    logging.getLogger().setLevel(args.log_level)
    
    logger.info(f"Starting server on {args.host}:{args.port}")
    uvicorn.run(starlette_app, host=args.host, port=args.port)