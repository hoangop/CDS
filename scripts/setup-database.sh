#!/bin/bash
# Script setup database schema cho Cloud SQL

set -e

PROJECT_ID="cds-analyticsanalytivcs"
REGION="asia-southeast1"
INSTANCE_NAME="cds-db"
DB_PASSWORD="dxb5ktn1sNo2jTGfOvqK3hnXT"
CONNECTION_NAME="$PROJECT_ID:$REGION:$INSTANCE_NAME"

echo "🗄️  Setting up Cloud SQL Database Schema"
echo "Connection: $CONNECTION_NAME"
echo ""

# Check if cloud-sql-proxy exists
if [ ! -f "./cloud-sql-proxy" ]; then
    echo "❌ cloud-sql-proxy not found. Downloading..."
    curl -o cloud-sql-proxy https://storage.googleapis.com/cloud-sql-connectors/cloud-sql-proxy/v2.8.0/cloud-sql-proxy.darwin.amd64
    chmod +x cloud-sql-proxy
fi

echo "📋 Instructions:"
echo ""
echo "1. Open a NEW terminal window and run:"
echo "   cd $(pwd)"
echo "   ./cloud-sql-proxy $CONNECTION_NAME"
echo ""
echo "2. Keep that terminal running, then come back here and press Enter..."
read -p "Press Enter when cloud-sql-proxy is running in another terminal..."

echo ""
echo "3. Setting up database schema..."
export DATABASE_URL="postgresql://postgres:$DB_PASSWORD@127.0.0.1:5432/cds_db"

# Activate venv and run create_db.py
source venv/bin/activate
python data_pipeline/scripts/create_db.py

echo ""
echo "✅ Database schema created successfully!"
echo ""
echo "📝 Next steps:"
echo "   - You can now import data using:"
echo "     python data_pipeline/scripts/process_direct_pdf_to_db.py"
echo ""
echo "   - Or setup GitHub Secrets and deploy via CI/CD"

