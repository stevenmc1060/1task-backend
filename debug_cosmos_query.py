import json
from cosmos_config import cosmos_manager

# Initialize Cosmos DB connection
container = cosmos_manager.get_container()

# Query all habit documents
query = "SELECT * FROM c WHERE c.document_type = 'habit'"
habits = list(container.query_items(query=query, enable_cross_partition_query=True))

# Write to all_habits.json
with open("all_habits.json", "w") as f:
    json.dump(habits, f, indent=2, default=str)

print(f"Exported {len(habits)} habit documents to all_habits.json")
