#!/usr/bin/env python3
"""
Script to delete all habits for a specific user from Cosmos DB.
This will permanently remove all habit records for the specified user.
"""

import logging
import sys
from models import DocumentType, Habit
from generic_repository import generic_repository

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def delete_all_user_habits(user_id: str):
    """
    Delete all habits for a specific user from the database.
    
    Args:
        user_id (str): The user ID whose habits should be deleted
    
    Returns:
        tuple: (success_count, total_count, errors)
    """
    try:
        logger.info(f"Starting deletion process for user: {user_id}")
        
        # First, get all habits for the user
        habits = generic_repository.get_documents_by_user_and_type(user_id, DocumentType.HABIT, Habit)
        total_count = len(habits)
        
        logger.info(f"Found {total_count} habits to delete for user {user_id}")
        
        if total_count == 0:
            logger.info("No habits found for this user")
            return 0, 0, []
        
        # Confirm deletion
        print(f"\n⚠️  WARNING: You are about to delete {total_count} habits for user {user_id}")
        print("This action cannot be undone!")
        
        confirmation = input("Type 'DELETE' to confirm deletion: ")
        if confirmation != 'DELETE':
            logger.info("Deletion cancelled by user")
            return 0, total_count, ["Deletion cancelled by user"]
        
        success_count = 0
        errors = []
        
        # Delete each habit
        for i, habit in enumerate(habits, 1):
            try:
                logger.info(f"Deleting habit {i}/{total_count}: {habit.id} - {getattr(habit, 'title', 'No title')}")
                
                success = generic_repository.delete_document(habit.id, user_id)
                if success:
                    success_count += 1
                    logger.info(f"✅ Successfully deleted habit {habit.id}")
                else:
                    error_msg = f"Failed to delete habit {habit.id} - delete_document returned False"
                    logger.error(error_msg)
                    errors.append(error_msg)
                    
            except Exception as e:
                error_msg = f"Error deleting habit {habit.id}: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)
        
        logger.info(f"Deletion complete: {success_count}/{total_count} habits deleted successfully")
        
        if errors:
            logger.error(f"Encountered {len(errors)} errors:")
            for error in errors:
                logger.error(f"  - {error}")
        
        return success_count, total_count, errors
        
    except Exception as e:
        logger.error(f"Fatal error during deletion process: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return 0, 0, [f"Fatal error: {str(e)}"]

def main():
    """Main function"""
    # Your user ID from the conversation context
    user_id = "2da56370-78bc-4278-9ed3-c693615ba407"
    
    print(f"🗑️  Habit Deletion Tool")
    print(f"User ID: {user_id}")
    print("=" * 50)
    
    try:
        success_count, total_count, errors = delete_all_user_habits(user_id)
        
        print("\n" + "=" * 50)
        print("DELETION SUMMARY")
        print("=" * 50)
        print(f"Total habits found: {total_count}")
        print(f"Successfully deleted: {success_count}")
        print(f"Errors: {len(errors)}")
        
        if errors:
            print("\nERRORS:")
            for error in errors:
                print(f"  - {error}")
        
        if success_count == total_count and total_count > 0:
            print(f"\n✅ All {total_count} habits have been successfully deleted!")
        elif success_count > 0:
            print(f"\n⚠️  Partially successful: {success_count}/{total_count} habits deleted")
        else:
            print(f"\n❌ No habits were deleted")
        
    except KeyboardInterrupt:
        print("\n\n🛑 Deletion cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
