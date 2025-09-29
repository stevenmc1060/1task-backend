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
        self.tasks_container_name = os.getenv('COSMOS_CONTAINER_NAME', 'tasks')
        self.profiles_container_name = os.getenv('COSMOS_PROFILES_CONTAINER_NAME', 'user-profiles')
        self.preview_codes_container_name = os.getenv('COSMOS_PREVIEW_CODES_CONTAINER_NAME', 'preview-codes')
        
        if not self.endpoint or not self.key:
            raise ValueError("COSMOS_ENDPOINT and COSMOS_KEY environment variables must be set")


class CosmosDBManager:
    """CosmosDB connection and operations manager"""
    
    def __init__(self):
        self.config = CosmosDBConfig()
        self.client: Optional[CosmosClient] = None
        self.database: Optional[DatabaseProxy] = None
        self.tasks_container: Optional[ContainerProxy] = None
        self.profiles_container: Optional[ContainerProxy] = None
        self.preview_codes_container: Optional[ContainerProxy] = None
        
    def initialize(self):
        """Initialize CosmosDB client, database, and containers"""
        try:
            # Create CosmosDB client
            self.client = CosmosClient(self.config.endpoint, self.config.key)
            logger.info("CosmosDB client initialized successfully")
            
            # Create or get database
            self.database = self._create_database_if_not_exists()
            logger.info(f"Database '{self.config.database_name}' ready")
            
            # Create or get containers
            self.tasks_container = self._create_tasks_container_if_not_exists()
            logger.info(f"Tasks container '{self.config.tasks_container_name}' ready")
            
            self.profiles_container = self._create_profiles_container_if_not_exists()
            logger.info(f"Profiles container '{self.config.profiles_container_name}' ready")
            
            self.preview_codes_container = self._create_preview_codes_container_if_not_exists()
            logger.info(f"Preview codes container '{self.config.preview_codes_container_name}' ready")
            
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
    
    def _create_tasks_container_if_not_exists(self) -> ContainerProxy:
        """Create tasks container if it doesn't exist"""
        try:
            container = self.database.create_container(
                id=self.config.tasks_container_name,
                partition_key={'paths': ['/user_id'], 'kind': 'Hash'}
            )
            logger.info(f"Created tasks container: {self.config.tasks_container_name}")
        except CosmosResourceExistsError:
            container = self.database.get_container_client(self.config.tasks_container_name)
            logger.info(f"Using existing tasks container: {self.config.tasks_container_name}")
        
        return container
    
    def _create_profiles_container_if_not_exists(self) -> ContainerProxy:
        """Create user profiles container if it doesn't exist"""
        try:
            container = self.database.create_container(
                id=self.config.profiles_container_name,
                partition_key={'paths': ['/user_id'], 'kind': 'Hash'}
            )
            logger.info(f"Created profiles container: {self.config.profiles_container_name}")
        except CosmosResourceExistsError:
            container = self.database.get_container_client(self.config.profiles_container_name)
            logger.info(f"Using existing profiles container: {self.config.profiles_container_name}")
        
        return container
    
    def _create_preview_codes_container_if_not_exists(self) -> ContainerProxy:
        """Create preview codes container if it doesn't exist"""
        try:
            container = self.database.create_container(
                id=self.config.preview_codes_container_name,
                partition_key={'paths': ['/code'], 'kind': 'Hash'}
            )
            logger.info(f"Created preview codes container: {self.config.preview_codes_container_name}")
        except CosmosResourceExistsError:
            container = self.database.get_container_client(self.config.preview_codes_container_name)
            logger.info(f"Using existing preview codes container: {self.config.preview_codes_container_name}")
        
        return container
    
    def get_tasks_container(self) -> ContainerProxy:
        """Get the tasks container instance"""
        if not self.tasks_container:
            self.initialize()
        return self.tasks_container
    
    def get_profiles_container(self) -> ContainerProxy:
        """Get the profiles container instance"""
        if not self.profiles_container:
            self.initialize()
        return self.profiles_container
    
    def get_preview_codes_container(self) -> ContainerProxy:
        """Get the preview codes container instance"""
        if not self.preview_codes_container:
            self.initialize()
        return self.preview_codes_container


# Global instance
cosmos_manager = CosmosDBManager()
