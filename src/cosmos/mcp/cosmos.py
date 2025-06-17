# server.py

"""
This file contains the server for the Cosmos DB MCP service.
"""

import os
import logging
import sys

from typing import Any, Dict
from functools import lru_cache
from dotenv import load_dotenv
from mcp.server import Server
from mcp.types import Tool

from azure.core.exceptions import ResourceExistsError, ResourceNotFoundError
from azure.identity import DefaultAzureCredential
from azure.core.exceptions import AzureError
from azure.cosmos import CosmosClient, PartitionKey
from .tools import get_cosmosdb_tools

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

# Suppress Azure SDK logging and cosmosdb logging
logging.getLogger("azure").setLevel(logging.WARNING)
logging.getLogger("azure.cosmos").setLevel(logging.WARNING)

# Load environment variables
load_dotenv()

class CosmosDBServer(Server):
    def __init__(self):
        logger.info("Initializing Cosmos DB server...")

        # Initialize the Cosmos DB client
        self._credential = DefaultAzureCredential()

    @property
    def service_name(self) -> str:
        """
        Get the name of the service.
        """
        return "cosmosdb_mcp"

    @lru_cache(maxsize=None)
    def get_cosmos_client(self, account_name: str) -> CosmosClient:
        """
        Get the Cosmos DB client.
        """

        if not account_name:
            raise ValueError("Account name is required")

        cosmos_db_uri = f"https://{account_name}.documents.azure.com:443/"

        try:
            client = CosmosClient(
                url=cosmos_db_uri,
                credential=self._credential
            )
            return client
        except Exception as e:
            logger.error(f"Error initializing Cosmos DB client: {e}")
            raise e

    async def get_tools(self) -> list[Tool]:
        """
        Get the tools for the Cosmos DB server.

        Returns:
            list[Tool]: The tools for the Cosmos DB server.
        """
        return get_cosmosdb_tools()

    async def execute_tool(self, tool_name: str, tool_args: Dict[str, Any]) -> Any:
        """
        Execute a tool based on its name and arguments.

        Args:
            tool_name (str): The name of the tool to execute
            tool_args (Dict[str, Any]): Arguments for the tool

        Returns:
            Any: The result of the tool execution

        Raises:
            ValueError: If the tool is not supported or parameters are invalid
            RuntimeError: If the service is not properly initialized
        """
        try:
            if tool_name == "cosmosdb_account_list":
                account_name = tool_args["account_name"]
                if not account_name:
                    raise ValueError("Account name is required")

                return await self._list_accounts(account_name)

            elif tool_name == "cosmosdb_database_list":
                account_name = tool_args["account_name"]
                if not account_name:
                    raise ValueError("Account name is required")

                return await self._list_databases(account_name)

            elif tool_name == "cosmosdb_database_describe":
                account_name = tool_args["account_name"]
                database_name = tool_args["database_name"]
                if not account_name or not database_name:
                    raise ValueError("Account name and database name are required")

                return await self._describe_database(account_name, database_name)

            if tool_name == "cosmosdb_container_list":
                account_name = tool_args["account_name"]
                database_name = tool_args["database_name"]
                if not account_name or not database_name:
                    raise ValueError("Account name and database name are required")

                return await self._list_containers(account_name, database_name)

            elif tool_name == "cosmosdb_container_create":
                account_name = tool_args["account_name"]
                database_name = tool_args["database_name"]
                container_name = tool_args["container_name"]
                partition_key = tool_args["partition_key"]
                if not account_name or not database_name or not container_name or not partition_key:
                    raise ValueError("Account name, database name, container name, and partition key are required")

                return await self._create_container(account_name, database_name, container_name, partition_key)

            elif tool_name == "cosmosdb_container_describe":
                account_name = tool_args["account_name"]
                database_name = tool_args["database_name"]
                container_name = tool_args["container_name"]
                if not account_name or not database_name or not container_name:
                    raise ValueError("Account name, database name, and container name are required")

                return await self._describe_container(account_name, database_name, container_name)

            elif tool_name == "cosmosdb_container_delete":
                account_name = tool_args["account_name"]
                database_name = tool_args["database_name"]
                container_name = tool_args["container_name"]
                if not account_name or not database_name or not container_name:
                    raise ValueError("Account name, database name, and container name are required")

                return await self._delete_container(account_name, database_name, container_name)

            elif tool_name == "cosmosdb_item_create":
                account_name = tool_args["account_name"]
                database_name = tool_args["database_name"]
                container_name = tool_args["container_name"]
                item = tool_args["item"]
                if not account_name or not database_name or not container_name or not item:
                    raise ValueError("Account name, database name, container name, and item are required")

                return await self._create_item(account_name, database_name, container_name, item)

            elif tool_name == "cosmosdb_item_read":
                account_name = tool_args["account_name"]
                database_name = tool_args["database_name"]
                container_name = tool_args["container_name"]
                item_id = tool_args["item_id"]
                partition_key = tool_args["partition_key"]
                if not account_name or not database_name or not container_name or not item_id or not partition_key:
                    raise ValueError("Account name, database name, container name, item ID, and partition key are required")

                return await self._read_item(account_name, database_name, container_name, item_id, partition_key)

            elif tool_name == "cosmosdb_item_delete":
                account_name = tool_args["account_name"]
                database_name = tool_args["database_name"]
                container_name = tool_args["container_name"]
                item_id = tool_args["item_id"]
                partition_key = tool_args["partition_key"]

                if not account_name or not database_name or not container_name or not item_id or not partition_key:
                    raise ValueError("Account name, database name, container name, item ID, and partition key are required")

                return await self._delete_item(account_name, database_name, container_name, item_id, partition_key)

            elif tool_name == "cosmosdb_item_query":
                account_name = tool_args["account_name"]
                database_name = tool_args["database_name"]
                container_name = tool_args["container_name"]
                query = tool_args["query"]
                parameters = tool_args["parameters"]

                if not account_name or not database_name or not container_name or not query:
                    raise ValueError("Account name, database name, container name, and query are required")

                return await self._query_item(account_name, database_name, container_name, query, parameters)

            elif tool_name == "cosmosdb_item_replace":
                account_name = tool_args["account_name"]
                database_name = tool_args["database_name"]
                container_name = tool_args["container_name"]
                item_id = tool_args["item_id"]
                item = tool_args["item"]
                partition_key = tool_args["partition_key"]

                if not account_name or not database_name or not container_name or not item_id or not item or not partition_key:
                    raise ValueError("Account name, database name, container name, item ID, item, and partition key are required")

                return await self._replace_item(account_name, database_name, container_name, item_id, item, partition_key)

            elif tool_name == "cosmosdb_item_delete":
                account_name = tool_args["account_name"]
                database_name = tool_args["database_name"]
                container_name = tool_args["container_name"]
                item_id = tool_args["item_id"]
                partition_key = tool_args["partition_key"]

                if not account_name or not database_name or not container_name or not item_id or not partition_key:
                    raise ValueError("Account name, database name, container name, item ID, and partition key are required")

                return await self._delete_item(account_name, database_name, container_name, item_id, partition_key)

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

    async def _list_databases(self, account_name: str) -> Dict[str, Any]:
        """
        List the databases in the Cosmos DB.

        Args:
            account_name (str): The name of the account

        Returns:
            Dict[str, Any]: A dictionary containing the databases
        """
        logger.info(f"Listing databases for account: {account_name}")
        client = self.get_cosmos_client(account_name)
        databases = []
        database_list = client.list_databases()

        for database in database_list:
            databases.append({
                "name": database.id
            })
        logger.info(f"Databases: {databases}")
        return databases

    async def _describe_database(self, account_name: str, database_name: str) -> Dict[str, Any]:
        """
        Describe a database in the Cosmos DB.

        Args:
            account_name (str): The name of the account
            database_name (str): The name of the database

        Returns:
            Dict[str, Any]: A dictionary containing the database
        """
        logger.info(f"Describing database: {database_name} for account: {account_name}")
        client = self.get_cosmos_client(account_name)
        return client.get_database_client(database_name)

    async def _list_containers(self, account_name: str, database_name: str) -> Dict[str, Any]:
        """
        List the containers in the database.

        Args:
            database_name (str): The name of the database

        Returns:
            Dict[str, Any]: A dictionary containing the containers
        """
        logger.info(f"Listing containers for database: {database_name} for account: {account_name}")
        containers = []
        client = self.get_cosmos_client(account_name)
        container_list = client.get_database_client(database_name).list_containers()

        for container in container_list:
            containers.append(container)
        logger.info(f"Containers: {containers}")
        return containers

    async def _create_container(self, account_name: str, database_name: str, container_name: str, partition_key: str) -> Dict[str, Any]:
        """
        Create a container in the database.

        Args:
            database_name (str): The name of the database
            container_name (str): The name of the container
            partition_key (str): The partition key of the container

        Returns:
            Dict[str, Any]: A dictionary containing the container
        """
        logger.info(f"Creating container: {container_name} for database: {database_name} for account: {account_name}")
        client = self.get_cosmos_client(account_name)
        container = client.get_database_client(database_name).create_container_if_not_exists(
            id=container_name,
            partition_key=PartitionKey(path=partition_key)
        )
        logger.info(f"Container created: {container.to_dict()}")
        return container.to_dict()

    async def _describe_container(self, account_name: str, database_name: str, container_name: str) -> Dict[str, Any]:
        """
        Describe a container in the database.

        Args:
            database_name (str): The name of the database
            container_name (str): The name of the container

        Returns:
            Dict[str, Any]: A dictionary containing the container
        """
        logger.info(f"Describing container: {container_name} for database: {database_name} for account: {account_name}")
        client = self.get_cosmos_client(account_name)
        container = client.get_database_client(database_name).get_container_client(container_name)
        logger.info(f"Container description: {container.to_dict()}")
        return container.to_dict()

    async def _delete_container(self, account_name: str, database_name: str, container_name: str) -> Dict[str, Any]:
        """
        Delete a container in the database.

        Args:
            database_name (str): The name of the database
            container_name (str): The name of the container

        Returns:
            Dict[str, Any]: A dictionary containing the container
        """
        logger.info(f"Deleting container: {container_name} for database: {database_name} for account: {account_name}")
        client = self.get_cosmos_client(account_name)
        return client.get_database_client(database_name).delete_container(container_name)

    async def _create_item(self, account_name: str, database_name: str, container_name: str, item: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create an item in the container.

        Args:
            database_name (str): The name of the database
            container_name (str): The name of the container
            item (Dict[str, Any]): The item to create

        Returns:
            Dict[str, Any]: A dictionary containing the item
        """
        logger.info(f"Creating item: {item} for container: {container_name} for database: {database_name} for account: {account_name}")
        client = self.get_cosmos_client(account_name)
        return client.get_database_client(database_name).get_container_client(container_name).create_item(item)

    async def _read_item(self, account_name: str, database_name: str, container_name: str, item_id: str) -> Dict[str, Any]:
        """
        Read an item in the container.

        Args:
            database_name (str): The name of the database
            container_name (str): The name of the container
            item_id (str): The ID of the item

        Returns:
            Dict[str, Any]: A dictionary containing the item
        """
        logger.info(f"Reading item: {item_id} for container: {container_name} for database: {database_name} for account: {account_name}")
        client = self.get_cosmos_client(account_name)
        return client.get_database_client(database_name).get_container_client(container_name).read_item(item_id)

    async def _delete_item(self, account_name: str, database_name: str, container_name: str, item_id: str) -> Dict[str, Any]:
        """
        Delete an item in the container.

        Args:
            database_name (str): The name of the database
            container_name (str): The name of the container
            item_id (str): The ID of the item

        Returns:
            Dict[str, Any]: A dictionary containing the item
        """
        logger.info(f"Deleting item: {item_id} for container: {container_name} for database: {database_name} for account: {account_name}")
        client = self.get_cosmos_client(account_name)
        return client.get_database_client(database_name).get_container_client(container_name).delete_item(item_id)

    async def _query_item(self, account_name: str, database_name: str, container_name: str, query: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Query an item in the container.

        Args:
            database_name (str): The name of the database
            container_name (str): The name of the container
            query (str): The query to execute
            parameters (Dict[str, Any]): The parameters to pass to the query

        Returns:
            Dict[str, Any]: A dictionary containing the items
        """
        logger.info(f"Querying item: {query} for container: {container_name} for database: {database_name} for account: {account_name}")
        client = self.get_cosmos_client(account_name)
        return client.get_database_client(database_name).get_container_client(container_name).query_items(query, parameters)

    async def _replace_item(self, account_name: str, database_name: str, container_name: str, item_id: str, item: Dict[str, Any], partition_key: str) -> Dict[str, Any]:
        """
        Replace an item in the container.

        Args:
            database_name (str): The name of the database
            container_name (str): The name of the container
            item_id (str): The ID of the item
            item (Dict[str, Any]): The item to replace
            partition_key (str): The partition key of the item

        Returns:
            Dict[str, Any]: A dictionary containing the item
        """
        logger.info(f"Replacing item: {item_id} for container: {container_name} for database: {database_name} for account: {account_name}")
        client = self.get_cosmos_client(account_name)
        return client.get_database_client(database_name).get_container_client(container_name).replace_item(item_id, item, partition_key)