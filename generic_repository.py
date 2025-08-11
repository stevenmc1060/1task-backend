"""
Generic repository for all document types in 1TaskAssistant application
"""
import logging
import uuid
from typing import List, Optional, Type, TypeVar
from datetime import datetime, date
from azure.cosmos import exceptions
from cosmos_config import cosmos_manager
from models import (
    BaseDocument, Task, YearlyGoal, QuarterlyGoal, WeeklyGoal, Habit, Project,
    DocumentType
)

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=BaseDocument)


class GenericRepository:
    """Generic repository for all document types"""
    
    def __init__(self):
        self.container = cosmos_manager.get_container()
    
    def create_document(self, document: T) -> T:
        """Create a new document"""
        try:
            # Generate ID if not provided
            if not document.id:
                document.id = str(uuid.uuid4())
            
            # Set timestamps
            document.created_at = datetime.utcnow()
            document.updated_at = datetime.utcnow()
            
            # Convert to dict for storage
            doc_dict = document.to_cosmos_dict()
            
            # Create in Cosmos DB
            created_item = self.container.create_item(body=doc_dict)
            
            # Convert back to model
            return type(document).from_cosmos_dict(created_item)
            
        except exceptions.CosmosHttpResponseError as e:
            logger.error(f"Error creating document: {e}")
            raise
    
    def get_documents_by_user_and_type(self, user_id: str, document_type: DocumentType, model_class: Type[T]) -> List[T]:
        """Get all documents of a specific type for a user"""
        try:
            query = "SELECT * FROM c WHERE c.user_id = @user_id AND c.document_type = @document_type"
            parameters = [
                {"name": "@user_id", "value": user_id},
                {"name": "@document_type", "value": document_type.value}
            ]
            
            items = list(self.container.query_items(
                query=query,
                parameters=parameters,
                partition_key=user_id
            ))
            
            return [model_class.from_cosmos_dict(item) for item in items]
            
        except exceptions.CosmosHttpResponseError as e:
            logger.error(f"Error querying documents: {e}")
            raise
    
    def get_document_by_id(self, document_id: str, user_id: str, model_class: Type[T]) -> Optional[T]:
        """Get a specific document by ID"""
        try:
            item = self.container.read_item(item=document_id, partition_key=user_id)
            return model_class.from_cosmos_dict(item)
            
        except exceptions.CosmosResourceNotFoundError:
            return None
        except exceptions.CosmosHttpResponseError as e:
            logger.error(f"Error reading document: {e}")
            raise
    
    def update_document(self, document_id: str, user_id: str, updates: dict, model_class: Type[T]) -> Optional[T]:
        """Update a document"""
        try:
            # First, get the existing document
            existing_item = self.container.read_item(item=document_id, partition_key=user_id)
            
            # Update fields
            for key, value in updates.items():
                if value is not None:
                    # Handle datetime fields specially
                    if key in ['completed_at', 'due_date', 'start_date', 'end_date', 'created_at', 'updated_at']:
                        if isinstance(value, str):
                            # Parse datetime string and convert to ISO format
                            try:
                                # Handle various datetime formats
                                if value.endswith('Z'):
                                    # Handle UTC timezone format
                                    parsed_dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
                                else:
                                    parsed_dt = datetime.fromisoformat(value)
                                existing_item[key] = parsed_dt.isoformat()
                            except ValueError as e:
                                logger.error(f"Error parsing datetime field {key} with value {value}: {e}")
                                raise ValueError(f"Invalid datetime format for field {key}: {value}")
                        elif isinstance(value, datetime):
                            existing_item[key] = value.isoformat()
                        else:
                            existing_item[key] = value
                    elif key in ['target_date', 'week_start_date']:
                        # Handle date fields
                        if isinstance(value, str):
                            try:
                                parsed_date = datetime.fromisoformat(value).date()
                                existing_item[key] = parsed_date.isoformat()
                            except ValueError as e:
                                logger.error(f"Error parsing date field {key} with value {value}: {e}")
                                raise ValueError(f"Invalid date format for field {key}: {value}")
                        else:
                            existing_item[key] = value
                    else:
                        # Handle other fields normally
                        existing_item[key] = value
                else:
                    # Allow clearing certain fields explicitly by sending null
                    # Currently supported: completed_at
                    if key in ['completed_at'] and key in existing_item:
                        del existing_item[key]
            
            # Update timestamp
            existing_item['updated_at'] = datetime.utcnow().isoformat()
            
            # Save to Cosmos DB
            updated_item = self.container.replace_item(item=document_id, body=existing_item)
            
            # Convert back to model
            return model_class.from_cosmos_dict(updated_item)
            
        except exceptions.CosmosResourceNotFoundError:
            return None
        except exceptions.CosmosHttpResponseError as e:
            logger.error(f"Error updating document: {e}")
            raise
    
    def delete_document(self, document_id: str, user_id: str) -> bool:
        """Delete a document"""
        try:
            self.container.delete_item(item=document_id, partition_key=user_id)
            return True
            
        except exceptions.CosmosResourceNotFoundError:
            return False
        except exceptions.CosmosHttpResponseError as e:
            logger.error(f"Error deleting document: {e}")
            raise


# Create a global instance
generic_repository = GenericRepository()
