#!/usr/bin/env python3
"""
Script to initialize preview codes in CosmosDB for OneTaskAssistant early access.
Run this script once to populate the database with the generated preview codes.
"""

import logging
import sys
import os
from datetime import datetime

# Add the current directory to Python path to import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from preview_code_repository import preview_code_repo
from cosmos_config import cosmos_manager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# The 25 generated preview codes
PREVIEW_CODES = [
    'WSHA61P9', 'F7WQUWYS', '1PHZ5MG3', 'K2TV2NU5', 'ZLQQX14D',
    'NV9I9IVY', 'YEW4C753', '72SQQPNK', 'RKAFLHWJ', 'I4QDZ6WY',
    'BUKEF4R8', '9Z1NKGD8', 'JG7RSHA2', 'GIV1SGIJ', '8U3YEW49',
    'DEBG4CU5', '4P2GI8WY', 'N5X19GBM', '5NGHZCGT', '7PTE4AMP',
    '24Q4YMG8', 'ECNLZ3NV', '6448ZFBK', 'PU9II8NN', '8TFQ95N6'
]


def initialize_preview_codes():
    """Initialize CosmosDB with preview codes"""
    try:
        logger.info("🚀 Starting preview code initialization...")
        
        # Initialize CosmosDB connection
        logger.info("📡 Initializing CosmosDB connection...")
        cosmos_manager.initialize()
        logger.info("✅ CosmosDB connection established")
        
        # Insert preview codes
        logger.info(f"📝 Inserting {len(PREVIEW_CODES)} preview codes...")
        
        inserted_count = 0
        existing_count = 0
        error_count = 0
        
        for code in PREVIEW_CODES:
            try:
                # Check if code already exists
                existing_code = preview_code_repo.get_preview_code(code)
                if existing_code:
                    logger.info(f"⚠️  Code already exists: {code}")
                    existing_count += 1
                    continue
                
                # Create the preview code
                preview_code_repo.create_preview_code(code, "system")
                logger.info(f"✅ Inserted: {code}")
                inserted_count += 1
                
            except Exception as e:
                logger.error(f"❌ Error inserting code {code}: {e}")
                error_count += 1
                continue
        
        # Print summary
        logger.info("\n🎉 Preview Code Initialization Complete!")
        logger.info("=" * 50)
        logger.info(f"📊 Total codes: {len(PREVIEW_CODES)}")
        logger.info(f"📊 Inserted: {inserted_count}")
        logger.info(f"📊 Already existed: {existing_count}")
        logger.info(f"📊 Errors: {error_count}")
        
        if error_count == 0:
            logger.info("🎊 All codes processed successfully!")
        else:
            logger.warning(f"⚠️  {error_count} codes had errors - check logs above")
        
        # Get and display stats
        try:
            stats = preview_code_repo.get_preview_code_stats()
            logger.info("\n📈 Current Preview Code Statistics:")
            logger.info(f"   Total codes in database: {stats['total_codes']}")
            logger.info(f"   Used codes: {stats['used_codes']}")
            logger.info(f"   Remaining codes: {stats['remaining_codes']}")
            logger.info(f"   Usage rate: {stats['usage_rate']}%")
        except Exception as e:
            logger.warning(f"Could not retrieve stats: {e}")
        
        logger.info("\n🎯 Next Steps:")
        logger.info("1. Deploy your updated Azure Functions")
        logger.info("2. Test the preview code validation endpoint")
        logger.info("3. Distribute codes to your early access users")
        logger.info("4. Monitor usage through the stats endpoint")
        
        return True
        
    except Exception as e:
        logger.error(f"💥 Failed to initialize preview codes: {e}")
        return False


def test_preview_code_validation():
    """Test the preview code validation functionality"""
    try:
        logger.info("\n🧪 Testing preview code validation...")
        
        # Test with the first code
        test_code = PREVIEW_CODES[0]
        test_user_id = "test-user-123"
        
        logger.info(f"Testing validation of code: {test_code}")
        
        is_valid, message, error_code = preview_code_repo.validate_and_use_preview_code(
            test_code, test_user_id
        )
        
        if is_valid:
            logger.info(f"✅ Code validation successful: {message}")
            
            # Try to use the same code again (should fail)
            is_valid2, message2, error_code2 = preview_code_repo.validate_and_use_preview_code(
                test_code, test_user_id
            )
            
            if not is_valid2 and error_code2 == "CODE_ALREADY_USED":
                logger.info(f"✅ Duplicate usage prevention working: {message2}")
            else:
                logger.error(f"❌ Duplicate usage prevention failed: {message2}")
        else:
            logger.error(f"❌ Code validation failed: {message} (Error: {error_code})")
        
        # Test invalid code
        is_valid3, message3, error_code3 = preview_code_repo.validate_and_use_preview_code(
            "INVALID123", test_user_id
        )
        
        if not is_valid3 and error_code3 == "INVALID_CODE":
            logger.info(f"✅ Invalid code detection working: {message3}")
        else:
            logger.error(f"❌ Invalid code detection failed: {message3}")
        
        logger.info("🧪 Testing complete!")
        
    except Exception as e:
        logger.error(f"💥 Testing failed: {e}")


if __name__ == "__main__":
    print("🎫 OneTaskAssistant Preview Code Initializer")
    print("=" * 50)
    
    # Check if we're in the right environment
    if not os.getenv('COSMOS_ENDPOINT') or not os.getenv('COSMOS_KEY'):
        print("❌ Error: COSMOS_ENDPOINT and COSMOS_KEY environment variables must be set")
        print("   Make sure your .env file is configured correctly")
        sys.exit(1)
    
    # Initialize preview codes
    success = initialize_preview_codes()
    
    if success:
        # Run basic tests
        test_preview_code_validation()
        print("\n🎉 Setup complete! Your preview code system is ready.")
    else:
        print("\n💥 Setup failed. Check the logs above for errors.")
        sys.exit(1)
