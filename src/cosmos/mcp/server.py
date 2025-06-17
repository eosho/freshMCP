# server.py

"""
This file contains the server for the Cosmos DB MCP service.
"""

import uvicorn
import argparse
from mcp.server.fastmcp import FastMCP
from .cosmos import CosmosDBServer

from mcp.server import Server

from starlette.applications import Starlette
from mcp.server.sse import SseServerTransport
from starlette.requests import Request
from starlette.routing import Mount, Route

# Global cosmos service instance
cosmos_service = CosmosDBServer()

mcp = FastMCP("cosmosdb_mcp")

# Static resource
@mcp.resource("config://version")
def get_version():
    """
    Get the version of the server.
    """
    return "1.0.0"

# Register basic resources and tools
@mcp.resource("echo://{message}")
def echo_resource(message: str) -> str:
    """
    Echo the message.
    """
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
    return f"Please process this message: {message}"

@mcp.tool(
  name="list_databases",
  description="List the databases in the account"
)
async def list_databases(account_name: str) -> list[str]:
    """
    List the databases in the account.
    Args:
        account_name (str): The name of the account

    Returns:
        list[str]: A list of the databases
    """
    return await cosmos_service._list_databases(account_name)

@mcp.tool(
  name="describe_database",
  description="Describe the database"
)
async def describe_database(account_name: str, database_name: str) -> dict:
    """
    Describe the database.
    Args:
        account_name (str): The name of the account
        database_name (str): The name of the database

    Returns:
        dict: A dictionary containing the database
    """
    return await cosmos_service._describe_database(account_name, database_name)

@mcp.tool(
  name="list_containers",
  description="List the containers in the database"
)
async def list_containers(account_name: str, database_name: str) -> list[str]:
    """
    List the containers in the database.
    Args:
        account_name (str): The name of the account
        database_name (str): The name of the database

    Returns:
        list[str]: A list of the containers
    """
    return await cosmos_service._list_containers(account_name, database_name)

@mcp.tool(
  name="create_container",
  description="Create a container in the database"
)
async def create_container(account_name: str, database_name: str, container_name: str, partition_key: str) -> dict:
    """
    Create a container in the database.
    Args:
        account_name (str): The name of the account
        database_name (str): The name of the database
        container_name (str): The name of the container
        partition_key (str): The partition key of the container

    Returns:
        dict: A dictionary containing the container
    """
    return await cosmos_service._create_container(account_name, database_name, container_name, partition_key)

@mcp.tool(
  name="delete_container",
  description="Delete a container in the database"
)
async def delete_container(account_name: str, database_name: str, container_name: str) -> dict:
    """
    Delete a container in the database.
    Args:
        account_name (str): The name of the account
        database_name (str): The name of the database
        container_name (str): The name of the container

    Returns:
        dict: A dictionary containing the container
    """
    return await cosmos_service._delete_container(account_name, database_name, container_name)

@mcp.tool(
  name="read_item",
  description="Read an item in the container"
)
async def read_item(account_name: str, database_name: str, container_name: str, item_id: str, partition_key: str) -> dict:
    """
    Read an item in the container.
    Args:
        account_name (str): The name of the account
        database_name (str): The name of the database
        container_name (str): The name of the container
        item_id (str): The ID of the item
        partition_key (str): The partition key of the item

    Returns:
        dict: A dictionary containing the item
    """
    return await cosmos_service._read_item(account_name, database_name, container_name, item_id, partition_key)

@mcp.tool(
  name="query_item",
  description="Query an item in the container"
)
async def query_item(account_name: str, database_name: str, container_name: str, query: str, parameters: dict) -> dict:
    """
    Query an item in the container.
    Args:
        account_name (str): The name of the account
        database_name (str): The name of the database
        container_name (str): The name of the container
        query (str): The query to execute
        parameters (dict): The parameters to pass to the query

    Returns:
        dict: A dictionary containing the item
    """
    return await cosmos_service._query_item(account_name, database_name, container_name, query, parameters)

def create_starlette_app(mcp_server: Server, *, debug: bool = False) -> Starlette:
    """Create a Starlette application that can server the provided mcp server with SSE.
    Args:
        mcp_server (Server): The MCP server to serve
        debug (bool): Whether to run in debug mode

    Returns:
        Starlette: The Starlette application
    """
    sse = SseServerTransport("/cosmos/messages/")

    async def handle_sse(request: Request) -> None:
        print(f"handling sse")

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
    )

mcp_server = mcp._mcp_server

# Bind SSE request handling to MCP server
starlette_app = create_starlette_app(mcp_server, debug=True)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run MCP SSE-based server')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=8001, help='Port to listen on')
    args = parser.parse_args()

    uvicorn.run(starlette_app, host=args.host, port=args.port)