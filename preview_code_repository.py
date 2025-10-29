"""
Preview Code Repository for 1TaskAssistant application
Handles CRUD operations for preview codes used in early access control
"""
import logging
from typing import Optional, List
from datetime import datetime
from azure.cosmos.exceptions import CosmosResourceNotFoundError
from models import PreviewCode, DocumentType
from cosmos_config import cosmos_manager

logger = logging.getLogger(__name__)


class PreviewCodeRepository:
    """Repository for preview code operations"""
    
    def __init__(self):
        self.container = cosmos_manager.get_preview_codes_container()
    
    def create_preview_code(self, code: str, user_id: str = "system") -> PreviewCode:
        """Create a new preview code"""
        try:
            preview_code = PreviewCode(
                code=code,
                user_id=user_id,  # System user for admin-created codes
                is_used=False,
                used_by_user_id=None,
                used_at=None
            )
            
            # Save to database
            code_dict = preview_code.to_cosmos_dict()
            result = self.container.create_item(body=code_dict)
            
            logger.info(f"Created preview code: {code}")
            return preview_code
            
        except Exception as e:
            logger.error(f"Error creating preview code {code}: {e}")
            raise
    
    def get_preview_code(self, code: str) -> Optional[PreviewCode]:
        """Get preview code by code string"""
        try:
            normalized_code = code.strip().upper()
            
            # Query for the preview code (using code as document ID)
            item = self.container.read_item(
                item=normalized_code,
                partition_key=normalized_code
            )
            
            return PreviewCode.from_cosmos_dict(item)
            
        except CosmosResourceNotFoundError:
            logger.info(f"Preview code not found: {code}")
            return None
        except Exception as e:
            logger.error(f"Error retrieving preview code {code}: {e}")
            raise
    
    def validate_and_use_preview_code(self, code: str, user_id: str) -> tuple[bool, str, Optional[str]]:
        """
        Validate preview code and mark as used if valid
        Returns: (is_valid, message, error_code)
        """
        try:
            normalized_code = code.strip().upper()
            
            # Get the preview code
            preview_code = self.get_preview_code(normalized_code)
            
            if not preview_code:
                return False, "Invalid preview code. Please check your code and try again.", "INVALID_CODE"
            
            if preview_code.is_used:
                return False, "This preview code has already been used", "CODE_ALREADY_USED"
            
            # Mark code as used
            preview_code.is_used = True
            preview_code.used_by_user_id = user_id
            preview_code.used_at = datetime.utcnow()
            preview_code.updated_at = datetime.utcnow()
            
            # Update in database
            code_dict = preview_code.to_cosmos_dict()
            self.container.replace_item(item=normalized_code, body=code_dict)
            
            logger.info(f"Preview code {normalized_code} validated and marked as used by user {user_id}")
            return True, "Preview code is valid", None
            
        except Exception as e:
            logger.error(f"Error validating preview code {code} for user {user_id}: {e}")
            return False, "Server error validating preview code", "SERVER_ERROR"
    
    def get_all_preview_codes(self) -> List[PreviewCode]:
        """Get all preview codes (admin function)"""
        try:
            query = "SELECT * FROM c WHERE c.document_type = @doc_type"
            parameters = [{"name": "@doc_type", "value": DocumentType.PREVIEW_CODE.value}]
            
            items = list(self.container.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=True
            ))
            
            return [PreviewCode.from_cosmos_dict(item) for item in items]
            
        except Exception as e:
            logger.error(f"Error retrieving all preview codes: {e}")
            raise
    
    def get_preview_code_stats(self) -> dict:
        """Get statistics about preview code usage"""
        try:
            all_codes = self.get_all_preview_codes()
            
            total_codes = len(all_codes)
            used_codes = len([code for code in all_codes if code.is_used])
            remaining_codes = total_codes - used_codes
            usage_rate = (used_codes / total_codes * 100) if total_codes > 0 else 0
            
            # Get recent usage (last 10 used codes)
            recent_usage = [
                {
                    "code": code.code,
                    "used_by": code.used_by_user_id,
                    "used_at": code.used_at.isoformat() if code.used_at else None
                }
                for code in sorted(
                    [c for c in all_codes if c.is_used],
                    key=lambda x: x.used_at or datetime.min,
                    reverse=True
                )[:10]
            ]
            
            return {
                "total_codes": total_codes,
                "used_codes": used_codes,
                "remaining_codes": remaining_codes,
                "usage_rate": round(usage_rate, 2),
                "recent_usage": recent_usage
            }
            
        except Exception as e:
            logger.error(f"Error getting preview code stats: {e}")
            raise
    
    def bulk_create_preview_codes(self, codes: List[str], user_id: str = "system") -> List[PreviewCode]:
        """Create multiple preview codes at once"""
        created_codes = []
        errors = []
        
        for code in codes:
            try:
                preview_code = self.create_preview_code(code, user_id)
                created_codes.append(preview_code)
            except Exception as e:
                errors.append(f"Error creating code {code}: {e}")
                continue
        
        if errors:
            logger.warning(f"Errors during bulk creation: {errors}")
        
        logger.info(f"Bulk created {len(created_codes)} preview codes")
        return created_codes

    def reset_preview_codes(self, reset_type: str = "mark_unused") -> dict:
        """Reset preview codes - either mark all as unused or delete all"""
        try:
            all_codes = self.get_all_preview_codes()
            affected_count = 0
            
            if reset_type == "delete_all":
                for preview_code in all_codes:
                    try:
                        self.container.delete_item(
                            item=preview_code.code,
                            partition_key=preview_code.code
                        )
                        affected_count += 1
                    except Exception as e:
                        logger.error(f"Error deleting preview code {preview_code.code}: {e}")
                        continue
                        
                message = f"Deleted {affected_count} preview codes"
                
            else:  # mark_unused
                for preview_code in all_codes:
                    if preview_code.is_used:
                        try:
                            # Reset the code to unused state
                            preview_code.is_used = False
                            preview_code.used_by_user_id = None
                            preview_code.used_at = None
                            preview_code.updated_at = datetime.utcnow()
                            
                            # Save to database
                            code_dict = preview_code.to_cosmos_dict()
                            self.container.replace_item(
                                item=preview_code.code,
                                body=code_dict
                            )
                            affected_count += 1
                        except Exception as e:
                            logger.error(f"Error resetting preview code {preview_code.code}: {e}")
                            continue
                            
                message = f"Reset {affected_count} preview codes to unused state"
            
            logger.info(f"Preview code reset completed: {message}")
            return {
                "success": True,
                "affected_count": affected_count,
                "message": message
            }
            
        except Exception as e:
            logger.error(f"Error during preview code reset: {e}")
            return {
                "success": False,
                "affected_count": 0,
                "message": f"Reset failed: {str(e)}"
            }


# Global instance
preview_code_repo = PreviewCodeRepository()
