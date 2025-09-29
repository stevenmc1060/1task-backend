"""
Repository layer for notes and folders operations with CosmosDB
"""
import logging
import uuid
from datetime import datetime
from typing import List, Optional
from azure.cosmos.exceptions import CosmosResourceNotFoundError
from models import Note, Folder
from cosmos_config import cosmos_manager

logger = logging.getLogger(__name__)


class NotesRepository:
    """Repository for notes CRUD operations"""
    
    def __init__(self):
        self.container = None
    
    def _get_container(self):
        """Get CosmosDB notes container instance"""
        if not self.container:
            self.container = cosmos_manager.get_notes_container()
        return self.container
    
    def create_note(self, note: Note) -> Note:
        """Create a new note in CosmosDB"""
        try:
            # Generate ID if not provided
            if not note.id:
                note.id = str(uuid.uuid4())
            
            # Ensure timestamps are set
            note.created_at = datetime.utcnow()
            note.updated_at = datetime.utcnow()
            
            container = self._get_container()
            note_dict = note.to_dict()
            
            # Create the document
            response = container.create_item(body=note_dict)
            logger.info(f"Created note with ID: {response['id']}")
            
            return Note.from_dict(response)
            
        except Exception as e:
            logger.error(f"Error creating note: {e}")
            raise
    
    def get_note(self, note_id: str, user_id: str) -> Optional[Note]:
        """Get a specific note by ID"""
        try:
            container = self._get_container()
            
            # Query with partition key for optimal performance
            query = "SELECT * FROM c WHERE c.id = @note_id AND c.user_id = @user_id"
            parameters = [
                {"name": "@note_id", "value": note_id},
                {"name": "@user_id", "value": user_id}
            ]
            
            items = list(container.query_items(
                query=query,
                parameters=parameters,
                partition_key=user_id
            ))
            
            if items:
                return Note.from_dict(items[0])
            return None
            
        except CosmosResourceNotFoundError:
            logger.info(f"Note not found: {note_id}")
            return None
        except Exception as e:
            logger.error(f"Error getting note: {e}")
            raise
    
    def list_notes(self, user_id: str, folder_id: Optional[str] = None) -> List[Note]:
        """List all notes for a user, optionally filtered by folder"""
        try:
            container = self._get_container()
            
            if folder_id:
                query = "SELECT * FROM c WHERE c.user_id = @user_id AND c.folder_id = @folder_id ORDER BY c.updated_at DESC"
                parameters = [
                    {"name": "@user_id", "value": user_id},
                    {"name": "@folder_id", "value": folder_id}
                ]
            else:
                query = "SELECT * FROM c WHERE c.user_id = @user_id ORDER BY c.updated_at DESC"
                parameters = [
                    {"name": "@user_id", "value": user_id}
                ]
            
            items = list(container.query_items(
                query=query,
                parameters=parameters,
                partition_key=user_id
            ))
            
            return [Note.from_dict(item) for item in items]
            
        except Exception as e:
            logger.error(f"Error listing notes: {e}")
            raise
    
    def update_note(self, note_id: str, user_id: str, note_data: dict) -> Optional[Note]:
        """Update an existing note"""
        try:
            # First get the existing note
            existing_note = self.get_note(note_id, user_id)
            if not existing_note:
                return None
            
            # Update the note data
            updated_data = existing_note.dict()
            updated_data.update(note_data)
            updated_data['updated_at'] = datetime.utcnow()
            
            container = self._get_container()
            
            # Replace the document
            response = container.replace_item(
                item=note_id,
                body=updated_data
            )
            
            logger.info(f"Updated note with ID: {note_id}")
            return Note.from_dict(response)
            
        except CosmosResourceNotFoundError:
            logger.info(f"Note not found for update: {note_id}")
            return None
        except Exception as e:
            logger.error(f"Error updating note: {e}")
            raise
    
    def delete_note(self, note_id: str, user_id: str) -> bool:
        """Delete a note"""
        try:
            container = self._get_container()
            
            # Delete the document
            container.delete_item(
                item=note_id,
                partition_key=user_id
            )
            
            logger.info(f"Deleted note with ID: {note_id}")
            return True
            
        except CosmosResourceNotFoundError:
            logger.info(f"Note not found for deletion: {note_id}")
            return False
        except Exception as e:
            logger.error(f"Error deleting note: {e}")
            raise
    
    def search_notes(self, user_id: str, search_term: str) -> List[Note]:
        """Search notes by title and content"""
        try:
            container = self._get_container()
            
            # Use CONTAINS for search functionality
            query = """
                SELECT * FROM c 
                WHERE c.user_id = @user_id 
                AND (CONTAINS(UPPER(c.title), UPPER(@search_term)) 
                     OR CONTAINS(UPPER(c.content), UPPER(@search_term)))
                ORDER BY c.updated_at DESC
            """
            parameters = [
                {"name": "@user_id", "value": user_id},
                {"name": "@search_term", "value": search_term}
            ]
            
            items = list(container.query_items(
                query=query,
                parameters=parameters,
                partition_key=user_id
            ))
            
            return [Note.from_dict(item) for item in items]
            
        except Exception as e:
            logger.error(f"Error searching notes: {e}")
            raise


class FoldersRepository:
    """Repository for folders CRUD operations"""
    
    def __init__(self):
        self.container = None
    
    def _get_container(self):
        """Get CosmosDB folders container instance"""
        if not self.container:
            self.container = cosmos_manager.get_folders_container()
        return self.container
    
    def create_folder(self, folder: Folder) -> Folder:
        """Create a new folder in CosmosDB"""
        try:
            # Generate ID if not provided
            if not folder.id:
                folder.id = str(uuid.uuid4())
            
            # Ensure timestamps are set
            folder.created_at = datetime.utcnow()
            folder.updated_at = datetime.utcnow()
            
            container = self._get_container()
            folder_dict = folder.to_dict()
            
            # Create the document
            response = container.create_item(body=folder_dict)
            logger.info(f"Created folder with ID: {response['id']}")
            
            return Folder.from_dict(response)
            
        except Exception as e:
            logger.error(f"Error creating folder: {e}")
            raise
    
    def get_folder(self, folder_id: str, user_id: str) -> Optional[Folder]:
        """Get a specific folder by ID"""
        try:
            container = self._get_container()
            
            # Query with partition key for optimal performance
            query = "SELECT * FROM c WHERE c.id = @folder_id AND c.user_id = @user_id"
            parameters = [
                {"name": "@folder_id", "value": folder_id},
                {"name": "@user_id", "value": user_id}
            ]
            
            items = list(container.query_items(
                query=query,
                parameters=parameters,
                partition_key=user_id
            ))
            
            if items:
                return Folder.from_dict(items[0])
            return None
            
        except CosmosResourceNotFoundError:
            logger.info(f"Folder not found: {folder_id}")
            return None
        except Exception as e:
            logger.error(f"Error getting folder: {e}")
            raise
    
    def list_folders(self, user_id: str, parent_id: Optional[str] = None) -> List[Folder]:
        """List all folders for a user, optionally filtered by parent"""
        try:
            container = self._get_container()
            
            if parent_id:
                query = "SELECT * FROM c WHERE c.user_id = @user_id AND c.parent_id = @parent_id ORDER BY c.name ASC"
                parameters = [
                    {"name": "@user_id", "value": user_id},
                    {"name": "@parent_id", "value": parent_id}
                ]
            else:
                query = "SELECT * FROM c WHERE c.user_id = @user_id AND (c.parent_id = null OR NOT IS_DEFINED(c.parent_id)) ORDER BY c.name ASC"
                parameters = [
                    {"name": "@user_id", "value": user_id}
                ]
            
            items = list(container.query_items(
                query=query,
                parameters=parameters,
                partition_key=user_id
            ))
            
            return [Folder.from_dict(item) for item in items]
            
        except Exception as e:
            logger.error(f"Error listing folders: {e}")
            raise
    
    def update_folder(self, folder_id: str, user_id: str, folder_data: dict) -> Optional[Folder]:
        """Update an existing folder"""
        try:
            # First get the existing folder
            existing_folder = self.get_folder(folder_id, user_id)
            if not existing_folder:
                return None
            
            # Update the folder data
            updated_data = existing_folder.dict()
            updated_data.update(folder_data)
            updated_data['updated_at'] = datetime.utcnow()
            
            container = self._get_container()
            
            # Replace the document
            response = container.replace_item(
                item=folder_id,
                body=updated_data
            )
            
            logger.info(f"Updated folder with ID: {folder_id}")
            return Folder.from_dict(response)
            
        except CosmosResourceNotFoundError:
            logger.info(f"Folder not found for update: {folder_id}")
            return None
        except Exception as e:
            logger.error(f"Error updating folder: {e}")
            raise
    
    def delete_folder(self, folder_id: str, user_id: str) -> bool:
        """Delete a folder"""
        try:
            container = self._get_container()
            
            # Delete the document
            container.delete_item(
                item=folder_id,
                partition_key=user_id
            )
            
            logger.info(f"Deleted folder with ID: {folder_id}")
            return True
            
        except CosmosResourceNotFoundError:
            logger.info(f"Folder not found for deletion: {folder_id}")
            return False
        except Exception as e:
            logger.error(f"Error deleting folder: {e}")
            raise


# Global instances
notes_repository = NotesRepository()
folders_repository = FoldersRepository()
