# search.py

"""
This file contains the server for the AI Search MCP service.
"""

import os
import logging
import sys

from typing import Any, Dict, List
from functools import lru_cache
from dotenv import load_dotenv
from mcp.server import Server
from mcp.types import Tool

from azure.core.exceptions import ResourceExistsError, ResourceNotFoundError
from azure.identity import DefaultAzureCredential
from azure.core.exceptions import AzureError
from azure.search.documents import SearchClient
from azure.search.documents.models import QueryType
from azure.search.documents.indexes import SearchIndexClient
from tools import get_search_tools

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

# Suppress Azure SDK logging
logging.getLogger("azure").setLevel(logging.WARNING)

# Load environment variables
load_dotenv()

class SearchServer(Server):
    def __init__(self):
        logger.info("Initializing Search server...")
        self._credential = DefaultAzureCredential()

    @property
    def service_name(self) -> str:
        """Get the name of the service."""
        return "search_mcp"

    @lru_cache(maxsize=None)
    def get_search_client(self, service_name: str, index_name: str) -> SearchClient:
        """Get the Search client for querying documents.

        Args:
            service_name (str): The name of the service
            index_name (str): The name of the index

        Returns:
            SearchClient: The Search client
        """
        search_service_name = service_name or os.getenv("SEARCH_SERVICE_NAME")
        if not search_service_name:
            raise ValueError("SEARCH_SERVICE_NAME environment variable is not set")

        search_endpoint = f"https://{search_service_name}.search.windows.net"

        try:
            client = SearchClient(
                endpoint=search_endpoint,
                index_name=index_name,
                credential=self._credential
            )
            return client
        except Exception as e:
            logger.error(f"Error initializing Search client: {e}")
            raise e

    @lru_cache(maxsize=None)
    def get_index_client(self, service_name: str) -> SearchIndexClient:
        """Get the SearchIndexClient for managing indexes.

        Args:
            service_name (str): The name of the service

        Returns:
            SearchIndexClient: The SearchIndexClient
        """
        search_service_name = service_name or os.getenv("SEARCH_SERVICE_NAME")
        if not search_service_name:
            raise ValueError("SEARCH_SERVICE_NAME environment variable is not set")

        search_endpoint = f"https://{search_service_name}.search.windows.net"

        try:
            client = SearchIndexClient(
                endpoint=search_endpoint,
                credential=self._credential
            )
            return client
        except Exception as e:
            logger.error(f"Error initializing SearchIndexClient: {e}")
            raise e

    async def get_tools(self) -> list[Tool]:
        """Get the tools for the Search server."""
        return get_search_tools()

    async def execute_tool(self, tool_name: str, tool_args: Dict[str, Any]) -> Any:
        """Execute a tool based on its name and arguments.

        Args:
            tool_name (str): The name of the tool to execute
            tool_args (Dict[str, Any]): Arguments for the tool

        Returns:
            Any: The result of the tool execution
        """
        try:
            if tool_name == "search_index_list":
                service_name = tool_args["service_name"]
                if not service_name:
                    raise ValueError("Service name is required")

                return await self._list_indexes(service_name)

            elif tool_name == "search_index_delete":
                service_name = tool_args["service_name"]
                index_name = tool_args["index_name"]
                if not service_name or not index_name:
                    raise ValueError("Service name and index name are required")

                return await self._delete_index(service_name, index_name)

            elif tool_name == "search_index_query":
                service_name = tool_args["service_name"]
                index_name = tool_args["index_name"]
                query = tool_args["query"]
                query_type = tool_args.get("query_type", "simple")
                if not service_name or not index_name or not query:
                    raise ValueError("Service name, index name, and query are required")

                return await self._query_index(service_name, index_name, query, query_type)

            elif tool_name == "search_index_describe":
                service_name = tool_args["service_name"]
                index_name = tool_args["index_name"]
                if not service_name or not index_name:
                    raise ValueError("Service name and index name are required")

                return await self._describe_index(service_name, index_name)

            else:
                raise ValueError(f"Unsupported tool: {tool_name}")

        except ResourceNotFoundError as e:
            error_msg = f"Resource not found: {str(e)}"
            logger.error(error_msg)
            return {"error": error_msg}

        except ResourceExistsError as e:
            error_msg = f"Resource already exists: {str(e)}"
            logger.error(error_msg)
            return {"error": error_msg}

        except AzureError as e:
            error_msg = f"Azure error: {str(e)}"
            logger.error(error_msg)
            return {"error": error_msg}

        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(error_msg)
            return {"error": error_msg}

    async def _list_indexes(self, service_name: str) -> List[str]:
        """List all search indexes in the account.

        Args:
            service_name (str): The name of the service

        Returns:
            List[str]: A list of search index names
        """
        client = self.get_index_client(service_name)
        indexes = client.list_indexes()
        return [index.name for index in indexes]

    async def _delete_index(self, service_name: str, index_name: str) -> Dict[str, Any]:
        """Delete a search index.

        Args:
            service_name (str): The name of the service
            index_name (str): The name of the index

        Returns:
            Dict[str, Any]: A dictionary with a message indicating the index was deleted
        """
        client = self.get_index_client(service_name)
        client.delete_index(index_name)
        return {"message": f"Index {index_name} deleted successfully"}

    async def _query_index(self, service_name: str, index_name: str, query: str, query_type: str = "simple") -> List[Dict[str, Any]]:
        """Query a search index with support for different query types.

        Args:
            service_name (str): The name of the service
            index_name (str): The name of the index
            query (str): The query to execute
            query_type (str): The type of query to execute

        Returns:
            List[Dict[str, Any]]: A list of search results
        """
        client = self.get_search_client(service_name, index_name)

        # Map query type to QueryType enum
        query_type_map = {
            "simple": QueryType.SIMPLE,
            "full": QueryType.FULL,
            "semantic": QueryType.SEMANTIC
        }

        # Execute search with specified query type
        results = client.search(
            search_text=query,
            query_type=query_type_map.get(query_type, QueryType.SIMPLE)
        )

        return [result.to_dict() for result in results]

    async def _describe_index(self, service_name: str, index_name: str) -> Dict[str, Any]:
        """Describe a search index including its fields and configuration.

        Args:
            service_name (str): The name of the service
            index_name (str): The name of the index

        Returns:
            Dict[str, Any]: A dictionary containing the index description
        """
        client = self.get_index_client(service_name)
        index = client.get_index(index_name)
        return index.to_dict()