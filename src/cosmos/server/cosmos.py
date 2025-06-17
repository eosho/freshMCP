import os
import logging
import sys

from typing import Any, Dict, TYPE_CHECKING
from functools import lru_cache
from dotenv import load_dotenv
from mcp.server import Server
from mcp.types import Tool

from azure.core.exceptions import ResourceExistsError, ResourceNotFoundError
from azure.identity import DefaultAzureCredential
from azure.core.exceptions import AzureError
from azure.cosmos import CosmosClient, PartitionKey
from tools import get_cosmosdb_tools
from ...config.config_factory import config
from ...telemetry import TelemetryService

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
        self._cosmos_client = config.get_cosmos_client()
        
        # Initialize telemetry
        self._telemetry = TelemetryService()
        self._telemetry.initialize()

    @property
    def service_name(self) -> str:
        """
        Get the name of the service.
        """
        return "cosmosdb_mcp"

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

            # ... rest of the tool execution code ...

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
        client = self._cosmos_client(account_name)
        databases = []
        database_list = client.list_databases()

        for database in database_list:
            databases.append({
                "name": database.id
            })
        return databases

    # ... rest of the methods ...

    def __del__(self):
        """Cleanup telemetry on server shutdown."""
        if hasattr(self, '_telemetry'):
            self._telemetry.shutdown() 