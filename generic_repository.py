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
        self.cosmos_manager = cosmos_manager
    
    def _get_container(self, document_type):
        """Get the appropriate container based on document type"""
        # Import here to avoid circular imports
        from models import UserProfile, OnboardingStatus, ChatSession, PreviewCode
        
        if document_type in [UserProfile, OnboardingStatus, ChatSession]:
            return self.cosmos_manager.get_profiles_container()
        elif document_type == PreviewCode:
            return self.cosmos_manager.get_preview_codes_container()
        else:
            return self.cosmos_manager.get_tasks_container()
    
    def create_document(self, document: T) -> T:
        """Create a new document"""
        try:
            logger.info(f"[REPO CREATE] Starting create_document for type: {type(document).__name__}")
            logger.info(f"[REPO CREATE] Document data: {document.model_dump()}")
            
            # Generate ID if not provided
            if not document.id:
                document.id = str(uuid.uuid4())
                logger.info(f"[REPO CREATE] Generated new ID: {document.id}")
            else:
                logger.info(f"[REPO CREATE] Using existing ID: {document.id}")
            
            # Set timestamps
            document.created_at = datetime.utcnow()
            document.updated_at = datetime.utcnow()
            logger.info(f"[REPO CREATE] Set timestamps: created={document.created_at}, updated={document.updated_at}")
            
            # Convert to dict for storage
            doc_dict = document.to_cosmos_dict()
            logger.info(f"[REPO CREATE] Cosmos dict: {doc_dict}")
            logger.info(f"[REPO CREATE] Document type in dict: {doc_dict.get('document_type')}")
            logger.info(f"[REPO CREATE] User ID in dict: {doc_dict.get('user_id')}")
            
            # Create in Cosmos DB
            container = self._get_container(type(document))
            logger.info(f"[REPO CREATE] About to call container.create_item")
            created_item = container.create_item(body=doc_dict)
            logger.info(f"[REPO CREATE] Cosmos DB create_item successful")
            logger.info(f"[REPO CREATE] Created item: {created_item}")
            
            # Convert back to model
            result = type(document).from_cosmos_dict(created_item)
            logger.info(f"[REPO CREATE] Successfully converted back to model: {result.model_dump()}")
            
            return result
            
        except exceptions.CosmosHttpResponseError as e:
            logger.error(f"[REPO CREATE] CosmosHttpResponseError: {e}")
            logger.error(f"[REPO CREATE] Error details: status_code={e.status_code}, message={e.message}")
            raise
        except Exception as e:
            logger.error(f"[REPO CREATE] Unexpected error: {e}")
            import traceback
            logger.error(f"[REPO CREATE] Traceback: {traceback.format_exc()}")
            raise
    
    def get_documents_by_user_and_type(self, user_id: str, document_type: DocumentType, model_class: Type[T]) -> List[T]:
        """Get all documents of a specific type for a user"""
        try:
            logger.info(f"[REPO GET] Starting get_documents_by_user_and_type")
            logger.info(f"[REPO GET] user_id: {user_id}")
            logger.info(f"[REPO GET] document_type: {document_type}")
            logger.info(f"[REPO GET] document_type.value: {document_type.value}")
            logger.info(f"[REPO GET] model_class: {model_class.__name__}")
            
            query = "SELECT * FROM c WHERE c.user_id = @user_id AND c.document_type = @document_type"
            parameters = [
                {"name": "@user_id", "value": user_id},
                {"name": "@document_type", "value": document_type.value}
            ]
            
            logger.info(f"[REPO GET] Query: {query}")
            logger.info(f"[REPO GET] Parameters: {parameters}")
            
            container = self._get_container(model_class)
            items = list(container.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=True  # Use cross-partition query instead of specific partition
            ))
            
            logger.info(f"[REPO GET] Raw query returned {len(items)} items")
            for i, item in enumerate(items):
                logger.info(f"[REPO GET] Item {i}: {item}")
            
            result = [model_class.from_cosmos_dict(item) for item in items]
            logger.info(f"[REPO GET] Successfully converted {len(result)} items to model objects")
            
            return result
            
        except exceptions.CosmosHttpResponseError as e:
            logger.error(f"[REPO GET] CosmosHttpResponseError: {e}")
            logger.error(f"[REPO GET] Error details: status_code={e.status_code}, message={e.message}")
            raise
        except Exception as e:
            logger.error(f"[REPO GET] Unexpected error: {e}")
            import traceback
            logger.error(f"[REPO GET] Traceback: {traceback.format_exc()}")
            raise
    
    def get_document_by_id(self, document_id: str, user_id: str, model_class: Type[T]) -> Optional[T]:
        """Get a specific document by ID"""
        try:
            container = self._get_container(model_class)
            item = container.read_item(item=document_id, partition_key=user_id)
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
            container = self._get_container(model_class)
            existing_item = container.read_item(item=document_id, partition_key=user_id)
            
            # Update fields
            for key, value in updates.items():
                if value is not None:
                    # Handle datetime fields specially
                    if key in ['completed_at', 'due_date', 'created_at', 'updated_at', 'last_completed_at']:
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
                    elif key in ['target_date', 'week_start_date', 'start_date', 'end_date']:
                        # Handle date fields
                        if isinstance(value, str):
                            try:
                                # Parse and validate the date, then store as string
                                parsed_date = datetime.fromisoformat(value).date()
                                existing_item[key] = parsed_date.isoformat()
                            except ValueError as e:
                                logger.error(f"Error parsing date field {key} with value {value}: {e}")
                                raise ValueError(f"Invalid date format for field {key}: {value}")
                        elif isinstance(value, date):
                            # If it's already a date object, convert to string
                            existing_item[key] = value.isoformat()
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
            updated_item = container.replace_item(item=document_id, body=existing_item)
            
            # Convert back to model
            return model_class.from_cosmos_dict(updated_item)
            
        except exceptions.CosmosResourceNotFoundError:
            return None
        except exceptions.CosmosHttpResponseError as e:
            logger.error(f"Error updating document: {e}")
            raise
    
    def delete_document(self, document_id: str, user_id: str, model_class: Type[T]) -> bool:
        """Delete a document"""
        try:
            container = self._get_container(model_class)
            container.delete_item(item=document_id, partition_key=user_id)
            return True
            
        except exceptions.CosmosResourceNotFoundError:
            return False
        except exceptions.CosmosHttpResponseError as e:
            logger.error(f"Error deleting document: {e}")
            raise


# Create a global instance
generic_repository = GenericRepository()
