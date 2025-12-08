#!/bin/bash
# Script setup GCP resources cho CDS Analytics

set -e

PROJECT_ID=${1:-""}
REGION=${2:-"asia-southeast1"}  # Default: Singapore (tốt cho Việt Nam)

if [ -z "$PROJECT_ID" ]; then
    echo "❌ Usage: ./scripts/setup-gcp.sh <PROJECT_ID> [REGION]"
    echo ""
    echo "   Examples:"
    echo "   ./scripts/setup-gcp.sh my-project-id asia-southeast1  # Singapore (khuyến nghị cho VN)"
    echo "   ./scripts/setup-gcp.sh my-project-id us-central1      # US (rẻ hơn nhưng latency cao)"
    echo ""
    echo "   Default region: asia-southeast1 (Singapore)"
    exit 1
fi

echo "🚀 Setting up GCP resources for CDS Analytics..."
echo "Project ID: $PROJECT_ID"
echo "Region: $REGION"
echo ""

# Set project
gcloud config set project $PROJECT_ID

# Check billing
echo "💳 Checking billing account..."
BILLING_ENABLED=$(gcloud billing projects describe $PROJECT_ID --format="value(billingEnabled)" 2>/dev/null || echo "False")
BILLING_ENABLED=$(echo "$BILLING_ENABLED" | tr '[:upper:]' '[:lower:]')

if [ "$BILLING_ENABLED" != "true" ]; then
    echo "⚠️  Billing is not enabled for this project."
    echo "   Please link a billing account first:"
    echo ""
    echo "   1. List billing accounts:"
    echo "      gcloud billing accounts list"
    echo ""
    echo "   2. Link billing account:"
    echo "      gcloud billing projects link $PROJECT_ID --billing-account=BILLING_ACCOUNT_ID"
    echo ""
    echo "   Or enable billing via Console:"
    echo "   https://console.cloud.google.com/billing/linkedaccount?project=$PROJECT_ID"
    exit 1
fi

echo "✅ Billing is enabled"

# Enable required APIs
echo "📦 Enabling required APIs..."
gcloud services enable \
    cloudbuild.googleapis.com \
    run.googleapis.com \
    sqladmin.googleapis.com \
    artifactregistry.googleapis.com \
    containerregistry.googleapis.com \
    secretmanager.googleapis.com

# Create Artifact Registry repository
echo "📦 Creating Artifact Registry repository..."
# Validate region format (must be full region name like asia-southeast1, not asia-southeast)
if [[ ! "$REGION" =~ ^[a-z]+-[a-z]+[0-9]+$ ]]; then
    echo "⚠️  Warning: Region format might be incorrect. Should be like 'asia-southeast1', not '$REGION'"
    echo "   Attempting to use region as-is..."
fi

if gcloud artifacts repositories describe cds-images --location=$REGION --quiet 2>/dev/null; then
    echo "Repository cds-images already exists in $REGION"
else
    gcloud artifacts repositories create cds-images \
        --repository-format=docker \
        --location=$REGION \
        --description="CDS Analytics Docker images"
fi

# Create Cloud SQL instance
echo "🗄️  Creating Cloud SQL instance..."
INSTANCE_NAME="cds-db"
DB_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)

# Check if instance already exists
if gcloud sql instances describe $INSTANCE_NAME --quiet 2>/dev/null; then
    echo "Instance $INSTANCE_NAME already exists, checking status..."
    INSTANCE_STATE=$(gcloud sql instances describe $INSTANCE_NAME --format="value(state)" 2>/dev/null || echo "UNKNOWN")
    
    if [ "$INSTANCE_STATE" = "PENDING_CREATE" ] || [ "$INSTANCE_STATE" = "PENDING" ]; then
        echo "⏳ Instance is still being created. Waiting for it to be ready (this may take 2-5 minutes)..."
        MAX_WAIT=300  # 5 minutes
        ELAPSED=0
        while [ "$INSTANCE_STATE" != "RUNNABLE" ] && [ $ELAPSED -lt $MAX_WAIT ]; do
            sleep 10
            ELAPSED=$((ELAPSED + 10))
            INSTANCE_STATE=$(gcloud sql instances describe $INSTANCE_NAME --format="value(state)" 2>/dev/null || echo "UNKNOWN")
            echo "   Current state: $INSTANCE_STATE (waited ${ELAPSED}s)..."
        done
        
        if [ "$INSTANCE_STATE" != "RUNNABLE" ]; then
            echo "⚠️  Warning: Instance not ready after $MAX_WAIT seconds. Continuing anyway..."
        else
            echo "✅ Instance is ready!"
        fi
    else
        echo "✅ Instance is ready (state: $INSTANCE_STATE)"
    fi
else
    echo "Creating new Cloud SQL instance..."
    gcloud sql instances create $INSTANCE_NAME \
        --database-version=POSTGRES_15 \
        --tier=db-f1-micro \
        --region=$REGION \
        --root-password=$DB_PASSWORD \
        --storage-type=SSD \
        --storage-size=10GB \
        --backup-start-time=03:00
    
    echo "⏳ Waiting for instance to be ready (this may take 2-5 minutes)..."
    MAX_WAIT=300  # 5 minutes
    ELAPSED=0
    INSTANCE_STATE="PENDING_CREATE"
    while [ "$INSTANCE_STATE" != "RUNNABLE" ] && [ $ELAPSED -lt $MAX_WAIT ]; do
        sleep 10
        ELAPSED=$((ELAPSED + 10))
        INSTANCE_STATE=$(gcloud sql instances describe $INSTANCE_NAME --format="value(state)" 2>/dev/null || echo "UNKNOWN")
        echo "   Current state: $INSTANCE_STATE (waited ${ELAPSED}s)..."
    done
    
    if [ "$INSTANCE_STATE" != "RUNNABLE" ]; then
        echo "⚠️  Warning: Instance not ready after $MAX_WAIT seconds. You may need to create database manually later."
    else
        echo "✅ Instance is ready!"
    fi
fi

# Get connection name
CONNECTION_NAME=$(gcloud sql instances describe $INSTANCE_NAME --format="value(connectionName)")

# Create database
echo "📊 Creating database..."
# Check if database exists first
if gcloud sql databases describe cds_db --instance=$INSTANCE_NAME --quiet 2>/dev/null; then
    echo "Database cds_db already exists, skipping creation..."
else
    gcloud sql databases create cds_db --instance=$INSTANCE_NAME
fi

# Create service account for GitHub Actions
echo "🔐 Creating service account for GitHub Actions..."
SA_NAME="github-actions"
SA_EMAIL="$SA_NAME@$PROJECT_ID.iam.gserviceaccount.com"

gcloud iam service-accounts create $SA_NAME \
    --display-name="GitHub Actions Service Account" \
    --description="Service account for GitHub Actions CI/CD" || echo "Service account already exists"

# Grant permissions
echo "🔑 Granting permissions..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SA_EMAIL" \
    --role="roles/run.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SA_EMAIL" \
    --role="roles/storage.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SA_EMAIL" \
    --role="roles/artifactregistry.writer"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SA_EMAIL" \
    --role="roles/cloudsql.client"

# Create and download key
echo "🔑 Creating service account key..."
gcloud iam service-accounts keys create key.json \
    --iam-account=$SA_EMAIL

echo ""
echo "✅ Setup completed!"
echo ""
echo "📋 Next steps:"
echo "1. Add the following secrets to your GitHub repository:"
echo "   - GCP_PROJECT_ID: $PROJECT_ID"
echo "   - GCP_SA_KEY: (content of key.json)"
echo "   - DATABASE_URL: postgresql://postgres:$DB_PASSWORD@/$INSTANCE_NAME?host=/cloudsql/$CONNECTION_NAME"
echo "   - CLOUD_SQL_INSTANCE: $CONNECTION_NAME"
echo ""
echo "2. Save the database password securely:"
echo "   DB_PASSWORD: $DB_PASSWORD"
echo ""
echo "3. Run database migrations:"
echo "   python data_pipeline/scripts/create_db.py"
echo ""
echo "⚠️  IMPORTANT: Keep key.json secure and add it to .gitignore!"

