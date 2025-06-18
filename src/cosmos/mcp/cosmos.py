# server.py

"""
This file contains the server for the Cosmos DB MCP service.
"""

import os
import logging
import sys

from typing import Any, Dict, Optional
from functools import lru_cache
from dotenv import load_dotenv
from mcp.server import Server
from mcp.types import Tool

from azure.core.exceptions import ResourceExistsError, ResourceNotFoundError, AzureError
from azure.identity import DefaultAzureCredential
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
    def name(self) -> str:
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
        logger.debug(f"Initializing Cosmos DB client for account: {account_name}")

        try:
            client = CosmosClient(
                url=cosmos_db_uri,
                credential=self._credential
            )
            return client
        except Exception as e:
            logger.error(f"Error initializing Cosmos DB client: {e}")
            raise AzureError(f"Failed to initialize Cosmos DB client: {str(e)}")

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
            logger.info(f"Executing tool: {tool_name} with args: {tool_args}")

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

            elif tool_name == "cosmosdb_database_create":
                account_name = tool_args["account_name"]
                database_name = tool_args["database_name"]
                if not account_name or not database_name:
                    raise ValueError("Account name and database name are required")

                return await self._create_database(account_name, database_name)

            elif tool_name == "cosmosdb_container_list":
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

            elif tool_name == "cosmosdb_container_delete":
                account_name = tool_args["account_name"]
                database_name = tool_args["database_name"]
                container_name = tool_args["container_name"]
                if not account_name or not database_name or not container_name:
                    raise ValueError("Account name, database name, and container name are required")

                return await self._delete_container(account_name, database_name, container_name)

            elif tool_name == "cosmosdb_item_read":
                account_name = tool_args["account_name"]
                database_name = tool_args["database_name"]
                container_name = tool_args["container_name"]
                item_id = tool_args["item_id"]
                partition_key = tool_args["partition_key"]
                if not account_name or not database_name or not container_name or not item_id or not partition_key:
                    raise ValueError("Account name, database name, container name, item ID, and partition key are required")

                return await self._read_item(account_name, database_name, container_name, item_id, partition_key)

            elif tool_name == "cosmosdb_item_query":
                account_name = tool_args["account_name"]
                database_name = tool_args["database_name"]
                container_name = tool_args["container_name"]
                query = tool_args["query"]
                parameters = tool_args["parameters"]

                if not account_name or not database_name or not container_name or not query:
                    raise ValueError("Account name, database name, container name, and query are required")

                return await self._query_items(account_name, database_name, container_name, query, parameters)

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

    async def _list_accounts(self, account_name: str) -> Dict[str, Any]:
        """
        List Cosmos DB accounts (placeholder implementation).
        Note: This is a placeholder as listing accounts typically requires management API access.
        Args:
            account_name (str): The name of the account
        Returns:
            Dict[str, Any]: A dictionary containing the account information
        """
        logger.info(f"Listing account: {account_name}")
        try:
            # This is a placeholder implementation
            # In a real scenario, you would use the Azure Management API to list accounts
            return {
                "accounts": [{
                    "id": account_name,
                    "name": account_name,
                    "type": "account",
                    "properties": {
                        "documentEndpoint": f"https://{account_name}.documents.azure.com:443/"
                    }
                }]
            }
        except Exception as e:
            logger.error(f"Error listing accounts: {e}")
            return {"error": str(e)}

    async def _create_database(self, account_name: str, database_name: str) -> Dict[str, Any]:
        """
        Create a new database in the Cosmos DB account.
        Args:
            account_name (str): The name of the account
            database_name (str): The name of the database
        Returns:
            Dict[str, Any]: A dictionary containing the database details
        """
        logger.info(f"Creating database: {database_name} for account: {account_name}")
        try:
            client = self.get_cosmos_client(account_name)
            database = client.create_database_if_not_exists(database_name)
            logger.info(f"Database created successfully: {database.id}")
            return {
                "id": database.id,
                "name": database.id,
                "type": "database",
                "properties": database.read()
            }
        except Exception as e:
            logger.error(f"Error creating database: {e}")
            return {"error": str(e)}

    async def _list_databases(self, account_name: str) -> Dict[str, Any]:
        """
        List the databases in the Cosmos DB.
        Args:
            account_name (str): The name of the account
        Returns:
            Dict[str, Any]: A dictionary containing the databases
        """
        logger.info(f"Listing databases for account: {account_name}")
        try:
            client = self.get_cosmos_client(account_name)
            databases = []
            database_list = client.list_databases()

            for database in database_list:
                databases.append({
                    "id": database["id"],
                    "name": database["id"],
                    "type": "database",
                    "properties": database
                })
            logger.info(f"Found {len(databases)} databases")
            return {"databases": databases}
        except Exception as e:
            logger.error(f"Error listing databases: {e}")
            return {"error": str(e)}

    async def _describe_database(self, account_name: str, database_name: str) -> Dict[str, Any]:
        """
        Describe a database in the Cosmos DB.

        Args:
            account_name (str): The name of the account
            database_name (str): The name of the database

        Returns:
            Dict[str, Any]: Database information
        """
        logger.info(f"Describing database: {database_name} for account: {account_name}")
        try:
            client = self.get_cosmos_client(account_name)
            database = client.get_database_client(database_name)
            return {
                "id": database.id,
                "name": database.id,
                "type": "database",
                "properties": database.read()
            }
        except Exception as e:
            logger.error(f"Error describing database: {e}")
            return {"error": str(e)}

    async def _list_containers(self, account_name: str, database_name: str) -> Dict[str, Any]:
        """
        List the containers in the database.
        Args:
            account_name (str): The name of the account
            database_name (str): The name of the database
        Returns:
            Dict[str, Any]: A dictionary containing the containers
        """
        logger.info(f"Listing containers for database: {database_name}")
        try:
            client = self.get_cosmos_client(account_name)
            database = client.get_database_client(database_name)
            containers = []
            container_list = database.list_containers()

            for container in container_list:
                containers.append({
                    "id": container["id"],
                    "name": container["id"],
                    "type": "container",
                    "properties": container
                })
            logger.info(f"Found {len(containers)} containers")
            return {"containers": containers}
        except Exception as e:
            logger.error(f"Error listing containers: {e}")
            return {"error": str(e)}

    async def _create_container(self, account_name: str, database_name: str, container_name: str, partition_key: str) -> Dict[str, Any]:
        """
        Create a container in the database.

        Args:
            account_name (str): The name of the account
            database_name (str): The name of the database
            container_name (str): The name of the container
            partition_key (str): The partition key of the container

        Returns:
            Dict[str, Any]: Container information
        """
        logger.info(f"Creating container: {container_name} for database: {database_name} for account: {account_name}")
        try:
            client = self.get_cosmos_client(account_name)
            database = client.get_database_client(database_name)
            container = database.create_container_if_not_exists(
                id=container_name,
                partition_key=PartitionKey(path=partition_key)
            )
            logger.info(f"Container created successfully: {container.id}")
            return {
                "id": container.id,
                "name": container.id,
                "type": "container",
                "properties": container.read()
            }
        except Exception as e:
            logger.error(f"Error creating container: {e}")
            return {"error": str(e)}

    async def _delete_container(self, account_name: str, database_name: str, container_name: str) -> Dict[str, Any]:
        """
        Delete a container in the database.

        Args:
            account_name (str): The name of the account
            database_name (str): The name of the database
            container_name (str): The name of the container

        Returns:
            Dict[str, Any]: Operation result
        """
        logger.info(f"Deleting container: {container_name} for database: {database_name} for account: {account_name}")
        try:
            client = self.get_cosmos_client(account_name)
            database = client.get_database_client(database_name)
            database.delete_container(container_name)
            logger.info(f"Container deleted successfully: {container_name}")
            return {
                "status": "success",
                "message": f"Container {container_name} deleted successfully"
            }
        except Exception as e:
            logger.error(f"Error deleting container: {e}")
            return {"error": str(e)}

    async def _read_item(self, account_name: str, database_name: str, container_name: str, item_id: str, partition_key: str) -> Dict[str, Any]:
        """
        Read an item in the container.

        Args:
            account_name (str): The name of the account
            database_name (str): The name of the database
            container_name (str): The name of the container
            item_id (str): The ID of the item
            partition_key (str): The partition key of the item

        Returns:
            Dict[str, Any]: Item data
        """
        logger.info(f"Reading item: {item_id} for container: {container_name} for database: {database_name}")
        try:
            client = self.get_cosmos_client(account_name)
            container = client.get_database_client(database_name).get_container_client(container_name)
            item = container.read_item(item_id, partition_key=partition_key)
            logger.info(f"Item read successfully: {item_id}")
            return {"item": item}
        except Exception as e:
            logger.error(f"Error reading item: {e}")
            return {"error": str(e)}

    async def _query_items(self, account_name: str, database_name: str, container_name: str, query: str, parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Query items in the container.
        Args:
            account_name (str): The name of the account
            database_name (str): The name of the database
            container_name (str): The name of the container
            query (str): The query to execute
            parameters (Optional[Dict[str, Any]]): The parameters for the query
        Returns:
            Dict[str, Any]: A dictionary containing the query results
        """
        logger.info(f"Querying items in container: {container_name} with query: {query}")
        try:
            client = self.get_cosmos_client(account_name)
            container = client.get_database_client(database_name).get_container_client(container_name)

            # Convert parameters to list of dicts if provided
            query_params = []
            if parameters:
                for key, value in parameters.items():
                    query_params.append({"name": key, "value": value})

            # Execute query
            items = []
            query_iterable = container.query_items(
                query=query,
                parameters=query_params,
                enable_cross_partition_query=True
            )

            for item in query_iterable:
                items.append(item)

            logger.info(f"Query returned {len(items)} items")
            return {"items": items}
        except Exception as e:
            logger.error(f"Error querying items: {e}")
            return {"error": str(e)}
