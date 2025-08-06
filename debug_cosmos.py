"""
Simple test script to debug CosmosDB connection
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("=== Environment Variables Test ===")
print(f"COSMOS_ENDPOINT: {os.getenv('COSMOS_ENDPOINT')}")
print(f"COSMOS_KEY: {'***' + str(os.getenv('COSMOS_KEY'))[-4:] if os.getenv('COSMOS_KEY') else 'None'}")
print(f"COSMOS_DATABASE_NAME: {os.getenv('COSMOS_DATABASE_NAME')}")
print(f"COSMOS_CONTAINER_NAME: {os.getenv('COSMOS_CONTAINER_NAME')}")

print("\n=== Testing CosmosDB Connection ===")
try:
    from azure.cosmos import CosmosClient
    
    endpoint = os.getenv('COSMOS_ENDPOINT')
    key = os.getenv('COSMOS_KEY')
    
    if not endpoint or not key:
        print("❌ Missing CosmosDB credentials")
        sys.exit(1)
    
    print("Creating CosmosDB client...")
    client = CosmosClient(endpoint, key)
    
    print("Testing connection...")
    # Try to list databases to test connection
    databases = list(client.list_databases())
    print(f"✅ Connection successful! Found {len(databases)} databases")
    
    for db in databases:
        print(f"  - Database: {db['id']}")
    
except Exception as e:
    print(f"❌ CosmosDB connection failed: {e}")
    sys.exit(1)

print("\n=== Testing Task Model ===")
try:
    from models import Task, TaskStatus, TaskPriority
    from datetime import datetime
    
    # Create a test task
    test_task = Task(
        title="Test Task",
        description="Test description",
        status=TaskStatus.PENDING,
        priority=TaskPriority.HIGH,
        user_id="test_user_123",
        tags=["test"]
    )
    
    print("✅ Task model creation successful")
    print(f"Task: {test_task.title}")
    
    # Test conversion to Cosmos dict
    cosmos_dict = test_task.to_cosmos_dict()
    print("✅ Cosmos dict conversion successful")
    
except Exception as e:
    print(f"❌ Task model test failed: {e}")
    sys.exit(1)

print("\n=== All tests passed! ===")
