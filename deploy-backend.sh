#!/bin/bash

# Deployment script for 1TaskAssistant Backend API to Azure Functions
# Usage: ./deploy-backend.sh

set -e

echo "🚀 Deploying 1TaskAssistant Backend to Azure Functions..."

# Configuration
RESOURCE_GROUP="1task-backend-rg"
FUNCTION_APP_NAME="1task-backend-api-$(date +%Y%m%d%H%M%S)"
LOCATION="East US"
STORAGE_ACCOUNT="1taskbe$(date +%Y%m%d%H%M)"

echo "📋 Deployment Configuration:"
echo "  Resource Group: $RESOURCE_GROUP"
echo "  Function App: $FUNCTION_APP_NAME"
echo "  Location: $LOCATION"
echo "  Storage Account: $STORAGE_ACCOUNT"

# Make sure we're in the backend directory
cd "$(dirname "$0")"

# Check if Azure CLI is installed and logged in
if ! command -v az &> /dev/null; then
    echo "❌ Azure CLI is not installed. Please install it first."
    exit 1
fi

if ! az account show &> /dev/null; then
    echo "❌ Not logged into Azure CLI. Please run 'az login' first."
    exit 1
fi

echo "✅ Azure CLI is ready"

# Create resource group
echo "🏗️  Creating resource group..."
az group create --name "$RESOURCE_GROUP" --location "$LOCATION" --output table

# Create storage account
echo "💾 Creating storage account..."
az storage account create \
    --name "$STORAGE_ACCOUNT" \
    --location "$LOCATION" \
    --resource-group "$RESOURCE_GROUP" \
    --sku Standard_LRS \
    --output table

# Create Function App
echo "⚡ Creating Azure Function App..."
az functionapp create \
    --resource-group "$RESOURCE_GROUP" \
    --consumption-plan-location "$LOCATION" \
    --runtime python \
    --runtime-version 3.11 \
    --functions-version 4 \
    --name "$FUNCTION_APP_NAME" \
    --storage-account "$STORAGE_ACCOUNT" \
    --output table

# Get connection string for CosmosDB (you'll need to set this manually)
echo "⚙️  Setting up application settings..."
echo "📝 NOTE: You'll need to manually configure these settings in Azure Portal:"
echo "   - COSMOS_ENDPOINT"
echo "   - COSMOS_KEY" 
echo "   - COSMOS_DATABASE_NAME"
echo "   - CORS origins"

# Deploy the function
echo "🚀 Deploying function code..."
func azure functionapp publish "$FUNCTION_APP_NAME" --python

echo "✅ Backend deployment complete!"
echo "🌐 Function App URL: https://$FUNCTION_APP_NAME.azurewebsites.net"
echo ""
echo "📋 Next steps:"
echo "1. Go to Azure Portal: https://portal.azure.com"
echo "2. Navigate to Function App: $FUNCTION_APP_NAME"
echo "3. Go to Configuration > Application Settings"
echo "4. Add your CosmosDB connection settings"
echo "5. Test the endpoints"
