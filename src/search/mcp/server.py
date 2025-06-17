# server.py

"""
This file contains the server for the AI Search MCP service.
"""

from typing import List, Dict, Any
import uvicorn
import argparse
from mcp.server.fastmcp import FastMCP
from search import SearchServer

from mcp.server import Server

from starlette.applications import Starlette
from mcp.server.sse import SseServerTransport
from starlette.requests import Request
from starlette.routing import Mount, Route

# Global search service instance
search_service = SearchServer()

mcp = FastMCP("search_mcp")

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
  name="search_index_list",
  description="List all search indexes",
)
async def search_index_list(service_name: str) -> List[str]:
    """
    List all search indexes.
    Args:
        service_name (str): The name of the service

    Returns:
        List[str]: A list of search index names
    """
    return await search_service._list_indexes(service_name)

@mcp.tool(
  name="search_index_delete",
  description="Delete a search index",
)
async def search_index_delete(service_name: str, index_name: str) -> Dict[str, Any]:
    """
    Delete a search index.
    Args:
        service_name (str): The name of the service
        index_name (str): The name of the index

    Returns:
        Dict[str, Any]: A dictionary with a message indicating the index was deleted
    """
    return await search_service._delete_index(service_name, index_name)

@mcp.tool(
  name="search_index_query",
  description="Query a search index",
)
async def search_index_query(service_name: str, index_name: str, query: str, query_type: str = "simple") -> List[Dict[str, Any]]:
    """
    Query a search index.
    Args:
        service_name (str): The name of the service
        index_name (str): The name of the index
        query (str): The query to execute
        query_type (str): The type of query to execute

    Returns:
        List[Dict[str, Any]]: A list of search results
    """
    return await search_service._query_index(service_name, index_name, query, query_type)

@mcp.tool(
  name="search_index_describe",
  description="Describe a search index",
)
async def search_index_describe(service_name: str, index_name: str) -> Dict[str, Any]:
    """
    Describe a search index.
    Args:
        service_name (str): The name of the service
        index_name (str): The name of the index

    Returns:
        Dict[str, Any]: A dictionary containing the index description
    """
    return await search_service._describe_index(service_name, index_name)

def create_starlette_app(mcp_server: Server, *, debug: bool = False) -> Starlette:
    """Create a Starlette application that can server the provided mcp server with SSE.
    Args:
        mcp_server (Server): The MCP server to serve
        debug (bool): Whether to run in debug mode

    Returns:
        Starlette: The Starlette application
    """
    sse = SseServerTransport("/search/messages/")

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
            Route("/search/sse", endpoint=handle_sse),
            Mount("/search/messages/", app=sse.handle_post_message),
        ],
    )

mcp_server = mcp._mcp_server

# Bind SSE request handling to MCP server
starlette_app = create_starlette_app(mcp_server, debug=True)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run MCP SSE-based server')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=8002, help='Port to listen on')
    args = parser.parse_args()

    uvicorn.run(starlette_app, host=args.host, port=args.port)