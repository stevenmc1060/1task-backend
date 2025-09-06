"""
User Profile Repository for 1TaskAssistant application
Handles CRUD operations for user profiles, onboarding status, and chat sessions
"""
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, date, timedelta
from azure.cosmos.exceptions import CosmosResourceNotFoundError
from models import (
    UserProfile, OnboardingStatus, ChatSession, ChatMessage, 
    OnboardingStep, DocumentType,
    CreateUserProfileRequest, UpdateUserProfileRequest
)
from cosmos_config import cosmos_manager

logger = logging.getLogger(__name__)


class UserProfileRepository:
    """Repository for user profile operations"""
    
    def __init__(self):
        self.container = cosmos_manager.get_profiles_container()
    
    def create_user_profile(self, user_id: str, request: CreateUserProfileRequest) -> UserProfile:
        """Create a new user profile"""
        try:
            # Check if profile already exists
            existing_profile = self.get_user_profile(user_id)
            if existing_profile:
                raise ValueError(f"User profile already exists for user_id: {user_id}")
            
            # Create new profile
            profile = UserProfile(
                user_id=user_id,
                display_name=request.display_name,
                email=request.email,
                first_name=request.first_name,
                last_name=request.last_name,
                location=request.location,
                timezone=request.timezone,
                bio=request.bio,
                primary_life_areas=request.primary_life_areas or [],
                life_area_priorities=request.life_area_priorities,
                preferred_greeting=request.preferred_greeting,
                communication_style=request.communication_style,
                oauth_provider=request.oauth_provider,
                oauth_id=request.oauth_id,
                # Onboarding fields
                first_run=request.first_run if hasattr(request, 'first_run') else True,
                onboarding_completed=request.onboarding_completed if hasattr(request, 'onboarding_completed') else False,
                interview_data=request.interview_data if hasattr(request, 'interview_data') else None,
            )
            
            # Save to database
            profile_dict = profile.to_cosmos_dict()
            result = self.container.create_item(body=profile_dict)
            
            # Update the profile with the generated ID
            profile.id = result['id']
            
            # Create initial onboarding status
            from models import OnboardingStatus, OnboardingStep
            onboarding_status = OnboardingStatus(
                user_id=user_id,
                current_step=OnboardingStep.WELCOME,
                completed_steps=[],
                is_completed=False,
                welcome_shown=False,
                interview_responses={}
            )
            
            # Save onboarding status
            onboarding_dict = onboarding_status.to_cosmos_dict()
            self.container.create_item(body=onboarding_dict)
            
            logger.info(f"Created user profile and onboarding status for user_id: {user_id}")
            return profile
            
        except Exception as e:
            logger.error(f"Error creating user profile: {e}")
            raise
    
    def get_user_profile(self, user_id: str) -> Optional[UserProfile]:
        """Get user profile by user_id"""
        try:
            query = "SELECT * FROM c WHERE c.user_id = @user_id AND c.document_type = @doc_type"
            parameters = [
                {"name": "@user_id", "value": user_id},
                {"name": "@doc_type", "value": DocumentType.USER_PROFILE.value}
            ]
            
            items = list(self.container.query_items(
                query=query,
                parameters=parameters,
                partition_key=user_id
            ))
            
            if items:
                return UserProfile.from_cosmos_dict(items[0])
            return None
            
        except Exception as e:
            logger.error(f"Error getting user profile: {e}")
            return None
    
    def update_user_profile(self, user_id: str, request: UpdateUserProfileRequest) -> Optional[UserProfile]:
        """Update an existing user profile"""
        try:
            # Get existing profile
            existing_profile = self.get_user_profile(user_id)
            if not existing_profile:
                return None
            
            # Update fields that are provided
            update_data = request.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                if hasattr(existing_profile, field):
                    setattr(existing_profile, field, value)
            
            # Update timestamp
            existing_profile.updated_at = datetime.utcnow()
            existing_profile.last_active = datetime.utcnow()
            
            # Save to database
            profile_dict = existing_profile.to_cosmos_dict()
            self.container.replace_item(item=existing_profile.id, body=profile_dict)
            
            logger.info(f"Updated user profile for user_id: {user_id}")
            return existing_profile
            
        except Exception as e:
            logger.error(f"Error updating user profile: {e}")
            return None
    
    def delete_user_profile(self, user_id: str) -> bool:
        """Delete user profile and all associated data"""
        try:
            # Get profile first
            profile = self.get_user_profile(user_id)
            if not profile:
                return False
            
            # Delete profile
            self.container.delete_item(item=profile.id, partition_key=user_id)
            
            # Also delete onboarding status and chat sessions
            onboarding_repo.delete_onboarding_status(user_id)
            chat_session_repo.delete_all_chat_sessions(user_id)
            
            logger.info(f"Deleted user profile and data for user_id: {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting user profile: {e}")
            return False


class OnboardingRepository:
    """Repository for onboarding status operations"""
    
    def __init__(self):
        self.container = cosmos_manager.get_profiles_container()
    
    def create_onboarding_status(self, user_id: str) -> OnboardingStatus:
        """Create initial onboarding status for new user"""
        try:
            onboarding = OnboardingStatus(user_id=user_id)
            
            # Save to database
            onboarding_dict = onboarding.to_cosmos_dict()
            result = self.container.create_item(body=onboarding_dict)
            
            # Update with generated ID
            onboarding.id = result['id']
            
            logger.info(f"Created onboarding status for user_id: {user_id}")
            return onboarding
            
        except Exception as e:
            logger.error(f"Error creating onboarding status: {e}")
            raise
    
    def get_onboarding_status(self, user_id: str) -> Optional[OnboardingStatus]:
        """Get onboarding status for user"""
        try:
            query = "SELECT * FROM c WHERE c.user_id = @user_id AND c.document_type = @doc_type"
            parameters = [
                {"name": "@user_id", "value": user_id},
                {"name": "@doc_type", "value": DocumentType.ONBOARDING_STATUS.value}
            ]
            
            items = list(self.container.query_items(
                query=query,
                parameters=parameters,
                partition_key=user_id
            ))
            
            if items:
                return OnboardingStatus.from_cosmos_dict(items[0])
            return None
            
        except Exception as e:
            logger.error(f"Error getting onboarding status: {e}")
            return None
    
    def update_onboarding_step(self, user_id: str, step: OnboardingStep, interview_data: Dict = None) -> Optional[OnboardingStatus]:
        """Update onboarding step and track progress"""
        try:
            # Get or create onboarding status
            onboarding = self.get_onboarding_status(user_id)
            if not onboarding:
                onboarding = self.create_onboarding_status(user_id)
            
            # Update current step
            onboarding.current_step = step
            
            # Add to completed steps if not already there
            if step not in onboarding.completed_steps:
                onboarding.completed_steps.append(step)
            
            # Store interview responses if provided
            if interview_data:
                # Handle special flags that should be set on the object itself
                if 'welcome_shown' in interview_data:
                    onboarding.welcome_shown = interview_data.pop('welcome_shown')
                
                # Update interview responses with remaining data
                onboarding.interview_responses.update(interview_data)
            
            # Check if onboarding is complete
            if step == OnboardingStep.COMPLETED:
                onboarding.is_completed = True
                onboarding.completed_at = datetime.utcnow()
            
            # Update timestamps
            onboarding.updated_at = datetime.utcnow()
            
            # Save to database
            onboarding_dict = onboarding.to_cosmos_dict()
            self.container.replace_item(item=onboarding.id, body=onboarding_dict)
            
            logger.info(f"Updated onboarding step to {step} for user_id: {user_id}")
            return onboarding
            
        except Exception as e:
            logger.error(f"Error updating onboarding step: {e}")
            return None
    
    def delete_onboarding_status(self, user_id: str) -> bool:
        """Delete onboarding status for user"""
        try:
            onboarding = self.get_onboarding_status(user_id)
            if not onboarding:
                return True
            
            self.container.delete_item(item=onboarding.id, partition_key=user_id)
            logger.info(f"Deleted onboarding status for user_id: {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting onboarding status: {e}")
            return False
    
    def reset_onboarding_status(self, user_id: str) -> Optional[OnboardingStatus]:
        """Reset onboarding status to initial state for user - useful for testing"""
        try:
            # Get existing onboarding status
            onboarding = self.get_onboarding_status(user_id)
            if not onboarding:
                # Create new one if it doesn't exist
                onboarding = self.create_onboarding_status(user_id)
                return onboarding
            
            # Reset to initial state
            onboarding.current_step = OnboardingStep.WELCOME
            onboarding.completed_steps = []
            onboarding.is_completed = False
            onboarding.completed_at = None
            onboarding.welcome_shown = False
            onboarding.interview_responses = {}
            onboarding.updated_at = datetime.utcnow()
            
            # Save to database
            onboarding_dict = onboarding.to_cosmos_dict()
            self.container.replace_item(item=onboarding.id, body=onboarding_dict)
            
            logger.info(f"Reset onboarding status for user_id: {user_id}")
            return onboarding
            
        except Exception as e:
            logger.error(f"Error resetting onboarding status: {e}")
            return None


class ChatSessionRepository:
    """Repository for chat session operations"""
    
    def __init__(self):
        self.container = cosmos_manager.get_profiles_container()
    
    def create_chat_session(self, user_id: str, title: str) -> ChatSession:
        """Create a new chat session"""
        try:
            session = ChatSession(
                user_id=user_id,
                session_title=title[:100]  # Limit title length
            )
            
            # Save to database
            session_dict = session.to_cosmos_dict()
            result = self.container.create_item(body=session_dict)
            
            # Update with generated ID
            session.id = result['id']
            
            logger.info(f"Created chat session '{title}' for user_id: {user_id}")
            return session
            
        except Exception as e:
            logger.error(f"Error creating chat session: {e}")
            raise
    
    def add_message_to_session(self, user_id: str, session_id: str, message: ChatMessage) -> Optional[ChatSession]:
        """Add a message to an existing chat session"""
        try:
            # Get session
            session = self.get_chat_session(user_id, session_id)
            if not session:
                return None
            
            # Add message
            session.messages.append(message)
            session.message_count = len(session.messages)
            session.updated_at = datetime.utcnow()
            
            # Save to database
            session_dict = session.to_cosmos_dict()
            self.container.replace_item(item=session.id, body=session_dict)
            
            logger.info(f"Added message to session {session_id} for user_id: {user_id}")
            return session
            
        except Exception as e:
            logger.error(f"Error adding message to session: {e}")
            return None
    
    def get_chat_session(self, user_id: str, session_id: str) -> Optional[ChatSession]:
        """Get specific chat session"""
        try:
            query = "SELECT * FROM c WHERE c.user_id = @user_id AND c.id = @session_id AND c.document_type = @doc_type"
            parameters = [
                {"name": "@user_id", "value": user_id},
                {"name": "@session_id", "value": session_id},
                {"name": "@doc_type", "value": DocumentType.CHAT_SESSION.value}
            ]
            
            items = list(self.container.query_items(
                query=query,
                parameters=parameters,
                partition_key=user_id
            ))
            
            if items:
                return ChatSession.from_cosmos_dict(items[0])
            return None
            
        except Exception as e:
            logger.error(f"Error getting chat session: {e}")
            return None
    
    def get_recent_chat_sessions(self, user_id: str, limit: int = 5) -> List[ChatSession]:
        """Get recent chat sessions for user (default last 5)"""
        try:
            query = """
            SELECT * FROM c 
            WHERE c.user_id = @user_id AND c.document_type = @doc_type 
            ORDER BY c.updated_at DESC 
            OFFSET 0 LIMIT @limit
            """
            parameters = [
                {"name": "@user_id", "value": user_id},
                {"name": "@doc_type", "value": DocumentType.CHAT_SESSION.value},
                {"name": "@limit", "value": limit}
            ]
            
            items = list(self.container.query_items(
                query=query,
                parameters=parameters,
                partition_key=user_id
            ))
            
            return [ChatSession.from_cosmos_dict(item) for item in items]
            
        except Exception as e:
            logger.error(f"Error getting recent chat sessions: {e}")
            return []
    
    def delete_chat_session(self, user_id: str, session_id: str) -> bool:
        """Delete a specific chat session"""
        try:
            session = self.get_chat_session(user_id, session_id)
            if not session:
                return False
            
            self.container.delete_item(item=session.id, partition_key=user_id)
            logger.info(f"Deleted chat session {session_id} for user_id: {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting chat session: {e}")
            return False
    
    def delete_all_chat_sessions(self, user_id: str) -> bool:
        """Delete all chat sessions for user"""
        try:
            sessions = self.get_recent_chat_sessions(user_id, limit=100)  # Get more to delete all
            
            for session in sessions:
                self.container.delete_item(item=session.id, partition_key=user_id)
            
            logger.info(f"Deleted {len(sessions)} chat sessions for user_id: {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting all chat sessions: {e}")
            return False


# Global instances
user_profile_repo = UserProfileRepository()
onboarding_repo = OnboardingRepository()
chat_session_repo = ChatSessionRepository()
