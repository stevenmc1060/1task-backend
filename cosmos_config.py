"""
CosmosDB configuration and connection management for 1TaskAssistant
"""
import os
import logging
from typing import Optional
from azure.cosmos import CosmosClient, DatabaseProxy, ContainerProxy
from azure.cosmos.exceptions import CosmosResourceNotFoundError, CosmosResourceExistsError
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class CosmosDBConfig:
    """Configuration class for CosmosDB connection"""
    
    def __init__(self):
        self.endpoint = os.getenv('COSMOS_ENDPOINT')
        self.key = os.getenv('COSMOS_KEY')
        self.database_name = os.getenv('COSMOS_DATABASE_NAME', '1task-db')
        self.container_name = os.getenv('COSMOS_CONTAINER_NAME', 'tasks')
        
        if not self.endpoint or not self.key:
            raise ValueError("COSMOS_ENDPOINT and COSMOS_KEY environment variables must be set")


class CosmosDBManager:
    """CosmosDB connection and operations manager"""
    
    def __init__(self):
        self.config = CosmosDBConfig()
        self.client: Optional[CosmosClient] = None
        self.database: Optional[DatabaseProxy] = None
        self.container: Optional[ContainerProxy] = None
        
    def initialize(self):
        """Initialize CosmosDB client, database, and container"""
        try:
            # Create CosmosDB client
            self.client = CosmosClient(self.config.endpoint, self.config.key)
            logger.info("CosmosDB client initialized successfully")
            
            # Create or get database
            self.database = self._create_database_if_not_exists()
            logger.info(f"Database '{self.config.database_name}' ready")
            
            # Create or get container
            self.container = self._create_container_if_not_exists()
            logger.info(f"Container '{self.config.container_name}' ready")
            
        except Exception as e:
            logger.error(f"Failed to initialize CosmosDB: {e}")
            raise
    
    def _create_database_if_not_exists(self) -> DatabaseProxy:
        """Create database if it doesn't exist"""
        try:
            database = self.client.create_database(id=self.config.database_name)
            logger.info(f"Created database: {self.config.database_name}")
        except CosmosResourceExistsError:
            database = self.client.get_database_client(self.config.database_name)
            logger.info(f"Using existing database: {self.config.database_name}")
        
        return database
    
    def _create_container_if_not_exists(self) -> ContainerProxy:
        """Create container if it doesn't exist"""
        try:
            # No throughput setting for serverless accounts
            container = self.database.create_container(
                id=self.config.container_name,
                partition_key={'paths': ['/user_id'], 'kind': 'Hash'}
            )
            logger.info(f"Created container: {self.config.container_name}")
        except CosmosResourceExistsError:
            container = self.database.get_container_client(self.config.container_name)
            logger.info(f"Using existing container: {self.config.container_name}")
        
        return container
    
    def get_container(self) -> ContainerProxy:
        """Get the container instance"""
        if not self.container:
            self.initialize()
        return self.container


# Global instance
cosmos_manager = CosmosDBManager()
