# server.py

"""
This file contains the server for the AI Search MCP service.
"""

import logging
import sys
from typing import List, Dict, Any, Optional
import uvicorn
import argparse
from mcp.server.fastmcp import FastMCP
from .search import SearchServer
from mcp.server import Server
from mcp.server.sse import SseServerTransport
from starlette.applications import Starlette
from starlette.routing import Mount, Route
from starlette.requests import Request

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

# Global search service instance
search_service = SearchServer()

# Initialize MCP server
mcp = FastMCP("search_mcp")

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
    name="search_index_create",
    description="Create a search index with fields for id, content, metadata, title, and created_at"
)
async def search_index_create(service_name: str, index_name: str) -> Dict[str, Any]:
    """
    Create a search index.
    Args:
        service_name (str): The name of the service
        index_name (str): The name of the index
    Returns:
        Dict[str, Any]: A dictionary with a message indicating the index was created
    """
    return await search_service.execute_tool("search_index_create", {
        "service_name": service_name,
        "index_name": index_name
    })

@mcp.tool(
    name="search_index_list",
    description="List all search indexes in the account"
)
async def search_index_list(service_name: str) -> List[str]:
    """
    List all search indexes.
    Args:
        service_name (str): The name of the service
    Returns:
        List[str]: A list of search index names
    """
    return await search_service.execute_tool("search_index_list", {
        "service_name": service_name
    })

@mcp.tool(
    name="search_index_delete",
    description="Delete a search index"
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
    return await search_service.execute_tool("search_index_delete", {
        "service_name": service_name,
        "index_name": index_name
    })

@mcp.tool(
    name="search_index_query",
    description="Query a search index with support for different query types (simple, full, semantic)"
)
async def search_index_query(
    service_name: str,
    index_name: str,
    query: str,
    query_type: str = "simple"
) -> List[Dict[str, Any]]:
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
    return await search_service.execute_tool("search_index_query", {
        "service_name": service_name,
        "index_name": index_name,
        "query": query,
        "query_type": query_type
    })

@mcp.tool(
    name="search_index_describe",
    description="Describe a search index including its fields and configuration"
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
    return await search_service.execute_tool("search_index_describe", {
        "service_name": service_name,
        "index_name": index_name
    })

def create_app(mcp_server: Server, *, debug: bool = False) -> Starlette:
    """Create a Starlette application that can server the provided mcp server with SSE."""
    sse = SseServerTransport("/search/messages/")

    async def handle_sse(request: Request) -> None:
        async with sse.connect_sse(
                request.scope,
                request.receive,
                request._send,  # noqa: SLF001
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

if __name__ == "__main__":
    mcp_server = mcp._mcp_server

    parser = argparse.ArgumentParser(description='Run MCP SSE-based server')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=8002, help='Port to listen on')
    parser.add_argument('--log-level', default='INFO', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                      help='Set the logging level')
    args = parser.parse_args()

    # Configure logging level from command line
    logging.getLogger().setLevel(args.log_level)

    logger.info(f"Starting server on {args.host}:{args.port}")

    # Bind SSE request handling to MCP server
    app = create_app(mcp_server, debug=True)
    uvicorn.run(app, host=args.host, port=args.port)