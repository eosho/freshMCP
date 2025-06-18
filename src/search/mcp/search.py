# search.py

"""
This file contains the server for the AI Search MCP service.
"""

import os
import logging
import sys
from typing import Any, Dict, List, Optional
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
from azure.search.documents.indexes.models import (
    SearchIndex,
    SimpleField,
    SearchableField,
    SearchFieldDataType
)
from .tools import get_search_tools

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
    def name(self) -> str:
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
        if not service_name:
            raise ValueError("Service name is required")

        search_endpoint = f"https://{service_name}.search.windows.net"

        if not index_name:
            raise ValueError("Index name is required")

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
        if not service_name:
            raise ValueError("Service name is required")

        search_endpoint = f"https://{service_name}.search.windows.net"

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
            logger.info(f"Executing tool: {tool_name} with args: {tool_args}")

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

            elif tool_name == "search_index_create":
                service_name = tool_args["service_name"]
                index_name = tool_args["index_name"]
                if not service_name or not index_name:
                    raise ValueError("Service name and index name are required")

                return await self._create_index(service_name, index_name)

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

    async def _create_index(self, service_name: str, index_name: str) -> Dict[str, Any]:
        """Create a search index.

        Args:
            service_name (str): The name of the service
            index_name (str): The name of the index

        Returns:
            Dict[str, Any]: A dictionary with a message indicating the index was created
        """
        logger.info(f"Creating index: {index_name} for service: {service_name}")
        client = self.get_index_client(service_name)

        # Create fields using the proper Azure Search SDK models
        fields = [
            SimpleField(
                name="id",
                type=SearchFieldDataType.String,
                key=True,
                searchable=False
            ),
            SearchableField(
                name="content",
                type=SearchFieldDataType.String,
                searchable=True,
                filterable=False,
                sortable=False,
                facetable=False
            ),
            SearchableField(
                name="metadata",
                type=SearchFieldDataType.String,
                searchable=True,
                filterable=True,
                sortable=True,
                facetable=True
            ),
            SearchableField(
                name="title",
                type=SearchFieldDataType.String,
                searchable=True,
                filterable=True,
                sortable=True,
                facetable=False
            ),
            SimpleField(
                name="created_at",
                type=SearchFieldDataType.DateTimeOffset,
                filterable=True,
                sortable=True,
                facetable=False
            )
        ]

        # Create the index using the SDK model
        index = SearchIndex(
            name=index_name,
            fields=fields,
            scoring_profiles=[],
            default_scoring_profile=None,
            cors_options=None,
            suggesters=[],
            analyzers=[],
            tokenizers=[],
            token_filters=[],
            char_filters=[]
        )

        try:
            client.create_index(index)
            logger.info(f"Successfully created index: {index_name}")
            return {"message": f"Index {index_name} created successfully"}
        except Exception as e:
            logger.error(f"Failed to create index {index_name}: {str(e)}")
            raise

    async def _list_indexes(self, service_name: str) -> List[str]:
        """List all search indexes in the account.

        Args:
            service_name (str): The name of the service

        Returns:
            List[str]: A list of search index names
        """
        logger.info(f"Listing indexes for service: {service_name}")
        client = self.get_index_client(service_name)
        try:
            indexes = client.list_indexes()
            index_names = [index.name for index in indexes]
            logger.info(f"Found {len(index_names)} indexes: {index_names}")
            return index_names
        except Exception as e:
            logger.error(f"Failed to list indexes: {str(e)}")
            raise

    async def _delete_index(self, service_name: str, index_name: str) -> Dict[str, Any]:
        """Delete a search index.

        Args:
            service_name (str): The name of the service
            index_name (str): The name of the index

        Returns:
            Dict[str, Any]: A dictionary with a message indicating the index was deleted
        """
        logger.info(f"Deleting index: {index_name} for service: {service_name}")
        client = self.get_index_client(service_name)
        try:
            client.delete_index(index_name)
            logger.info(f"Successfully deleted index: {index_name}")
            return {"message": f"Index {index_name} deleted successfully"}
        except Exception as e:
            logger.error(f"Failed to delete index {index_name}: {str(e)}")
            raise

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
        logger.info(f"Querying index: {index_name} for service: {service_name} with query: {query}")
        client = self.get_search_client(service_name, index_name)

        # Map query type to QueryType enum
        query_type_map = {
            "simple": QueryType.SIMPLE,
            "full": QueryType.FULL,
            "semantic": QueryType.SEMANTIC
        }

        try:
            # Execute search with specified query type
            results = client.search(
                search_text=query,
                query_type=query_type_map.get(query_type, QueryType.SIMPLE)
            )

            # Convert results to list of dictionaries
            result_list = [result.to_dict() for result in results]
            logger.info(f"Found {len(result_list)} results")
            return result_list
        except Exception as e:
            logger.error(f"Failed to query index: {str(e)}")
            raise

    async def _describe_index(self, service_name: str, index_name: str) -> Dict[str, Any]:
        """Describe a search index including its fields and configuration.

        Args:
            service_name (str): The name of the service
            index_name (str): The name of the index

        Returns:
            Dict[str, Any]: A dictionary containing the index description
        """
        logger.info(f"Describing index: {index_name} for service: {service_name}")
        client = self.get_index_client(service_name)
        try:
            index = client.get_index(index_name)
            index_dict = index.to_dict()
            logger.info(f"Successfully retrieved index description for {index_name}")
            return index_dict
        except Exception as e:
            logger.error(f"Failed to describe index {index_name}: {str(e)}")
            raise