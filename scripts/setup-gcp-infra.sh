#!/usr/bin/env bash
# ==============================================================================
# GH Wealth Management AI Coach - Complete GCP Infrastructure Setup Script
# Configures VPC, Private Services Access, AlloyDB, Secret Manager, Cloud Run & Cloud Build
# ==============================================================================
set -euo pipefail

# ------------------------------------------------------------------------------
# Configuration Variables (Edit or pass via Environment)
# ------------------------------------------------------------------------------
PROJECT_ID="${PROJECT_ID:-artha-ai-wealth-coach}"
REGION="${REGION:-us-central1}"
VPC_NAME="${VPC_NAME:-wm-coach-vpc}"
SUBNET_NAME="${SUBNET_NAME:-wm-coach-subnet}"
SUBNET_CIDR="${SUBNET_CIDR:-10.0.0.0/24}"
PSA_RANGE_NAME="${PSA_RANGE_NAME:-alloydb-psa-range}"
ALLOYDB_CLUSTER="${ALLOYDB_CLUSTER:-wm-coach-alloydb-cluster}"
ALLOYDB_INSTANCE="${ALLOYDB_INSTANCE:-wm-coach-alloydb-primary}"
ARTIFACT_REPO="${ARTIFACT_REPO:-wm-coach-repo}"
BACKEND_SA="wm-coach-backend-sa"
FRONTEND_SA="wm-coach-frontend-sa"

# Secrets placeholders (can be overridden before running, or auto-generated)
GEMINI_API_KEY="${GEMINI_API_KEY:-YOUR_GEMINI_API_KEY_HERE}"
ALLOYDB_PASSWORD="${ALLOYDB_PASSWORD:-}"

if [ -z "$ALLOYDB_PASSWORD" ] || [ "$ALLOYDB_PASSWORD" = "YOUR_ALLOYDB_PASSWORD_HERE" ]; then
  ALLOYDB_PASSWORD=$(openssl rand -base64 16 | tr -dc 'a-zA-Z0-9_#-' | head -c 20)
  echo "Auto-generated secure AlloyDB password."
fi

echo "================================================================================"
echo "  Setting up GH Wealth Management Coach Infrastructure on Google Cloud"
echo "================================================================================"

if [ -z "$PROJECT_ID" ]; then
  echo "Error: PROJECT_ID is not set. Please set it using: export PROJECT_ID=\"your-gcp-project-id\""
  exit 1
fi

echo "Project ID:        $PROJECT_ID"
echo "Region:            $REGION"
echo "VPC Network:       $VPC_NAME"
echo "Subnet:            $SUBNET_NAME ($SUBNET_CIDR)"
echo "AlloyDB Cluster:   $ALLOYDB_CLUSTER"
echo ""

# ------------------------------------------------------------------------------
# Step 1: Set GCP Project & Region
# ------------------------------------------------------------------------------
echo "==> [1/9] Setting GCP Project and Compute Region..."
gcloud config set project "$PROJECT_ID"
gcloud config set compute/region "$REGION"

# ------------------------------------------------------------------------------
# Step 2: Enable Required APIs
# ------------------------------------------------------------------------------
echo "==> [2/9] Enabling Required Google Cloud APIs..."
gcloud services enable \
  run.googleapis.com \
  compute.googleapis.com \
  servicenetworking.googleapis.com \
  alloydb.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com \
  secretmanager.googleapis.com \
  aiplatform.googleapis.com \
  iam.googleapis.com

# ------------------------------------------------------------------------------
# Step 3: Create Custom VPC & Subnet for Direct VPC Egress
# ------------------------------------------------------------------------------
echo "==> [3/9] Configuring VPC Network and Subnet for Direct VPC Egress..."
if ! gcloud compute networks describe "$VPC_NAME" &>/dev/null; then
  echo "Creating VPC network: $VPC_NAME..."
  gcloud compute networks create "$VPC_NAME" --subnet-mode=custom
else
  echo "VPC network $VPC_NAME already exists."
fi

if ! gcloud compute networks subnets describe "$SUBNET_NAME" --region="$REGION" &>/dev/null; then
  echo "Creating Subnet: $SUBNET_NAME ($SUBNET_CIDR)..."
  gcloud compute networks subnets create "$SUBNET_NAME" \
    --network="$VPC_NAME" \
    --region="$REGION" \
    --range="$SUBNET_CIDR" \
    --enable-private-ip-google-access
else
  echo "Subnet $SUBNET_NAME already exists."
fi

# ------------------------------------------------------------------------------
# Step 4: Configure Private Services Access (PSA) for AlloyDB
# ------------------------------------------------------------------------------
echo "==> [4/9] Allocating IP Range and Peering for AlloyDB Private IP..."
if ! gcloud compute addresses describe "$PSA_RANGE_NAME" --global &>/dev/null; then
  gcloud compute addresses create "$PSA_RANGE_NAME" \
    --global \
    --purpose=VPC_PEERING \
    --prefix-length=16 \
    --network="$VPC_NAME"
else
  echo "PSA IP range $PSA_RANGE_NAME already exists."
fi

echo "Connecting Service Networking Peering to $VPC_NAME..."
gcloud services vpc-peerings connect \
  --service=servicenetworking.googleapis.com \
  --ranges="$PSA_RANGE_NAME" \
  --network="$VPC_NAME" || true

# ------------------------------------------------------------------------------
# Step 5: Create Secret Manager Secrets (Gemini API Key & AlloyDB Password)
# ------------------------------------------------------------------------------
echo "==> [5/9] Creating Secret Manager Secrets..."
# Gemini API Key Secret
if ! gcloud secrets describe gemini-api-key &>/dev/null; then
  echo "Creating secret: gemini-api-key (with placeholder)..."
  gcloud secrets create gemini-api-key --replication-policy="automatic"
  echo -n "$GEMINI_API_KEY" | gcloud secrets versions add gemini-api-key --data-file=-
else
  echo "Secret gemini-api-key already exists."
fi

# AlloyDB Password Secret
if ! gcloud secrets describe alloydb-password &>/dev/null; then
  echo "Creating secret: alloydb-password (with placeholder)..."
  gcloud secrets create alloydb-password --replication-policy="automatic"
  echo -n "$ALLOYDB_PASSWORD" | gcloud secrets versions add alloydb-password --data-file=-
else
  echo "Secret alloydb-password already exists."
fi

# ------------------------------------------------------------------------------
# Step 6: Create AlloyDB for PostgreSQL Cluster & Primary Instance
# ------------------------------------------------------------------------------
echo "==> [6/9] Provisioning AlloyDB for PostgreSQL Cluster & Instance (this may take 5-10 minutes)..."
if ! gcloud alloydb clusters describe "$ALLOYDB_CLUSTER" --region="$REGION" &>/dev/null; then
  echo "Creating AlloyDB Cluster: $ALLOYDB_CLUSTER..."
  gcloud alloydb clusters create "$ALLOYDB_CLUSTER" \
    --region="$REGION" \
    --network="$VPC_NAME" \
    --password="$ALLOYDB_PASSWORD"
else
  echo "AlloyDB Cluster $ALLOYDB_CLUSTER already exists."
fi

if ! gcloud alloydb instances describe "$ALLOYDB_INSTANCE" --cluster="$ALLOYDB_CLUSTER" --region="$REGION" &>/dev/null; then
  echo "Creating AlloyDB Primary Instance: $ALLOYDB_INSTANCE..."
  gcloud alloydb instances create "$ALLOYDB_INSTANCE" \
    --cluster="$ALLOYDB_CLUSTER" \
    --region="$REGION" \
    --instance-type=PRIMARY \
    --cpu-count=2
else
  echo "AlloyDB Primary Instance $ALLOYDB_INSTANCE already exists."
fi

ALLOYDB_IP=$(gcloud alloydb instances describe "$ALLOYDB_INSTANCE" \
  --cluster="$ALLOYDB_CLUSTER" \
  --region="$REGION" \
  --format="value(ipAddress)")
echo "AlloyDB Instance Private IP: $ALLOYDB_IP"

# ------------------------------------------------------------------------------
# Step 7: Create Artifact Registry Docker Repository
# ------------------------------------------------------------------------------
echo "==> [7/9] Creating Artifact Registry Repository..."
if ! gcloud artifacts repositories describe "$ARTIFACT_REPO" --location="$REGION" &>/dev/null; then
  gcloud artifacts repositories create "$ARTIFACT_REPO" \
    --repository-format=docker \
    --location="$REGION" \
    --description="Docker repo for GH WM Coach"
else
  echo "Artifact Registry repository $ARTIFACT_REPO already exists."
fi

# ------------------------------------------------------------------------------
# Step 8: Configure Service Accounts and IAM Roles
# ------------------------------------------------------------------------------
echo "==> [8/9] Creating Service Accounts & Binding Permissions..."
for SA in "$BACKEND_SA" "$FRONTEND_SA"; do
  if ! gcloud iam service-accounts describe "${SA}@${PROJECT_ID}.iam.gserviceaccount.com" &>/dev/null; then
    gcloud iam service-accounts create "$SA" --display-name="Service account for $SA"
  fi
done

# Backend SA permissions
gcloud secrets add-iam-policy-binding gemini-api-key \
  --member="serviceAccount:${BACKEND_SA}@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor" || true

gcloud secrets add-iam-policy-binding alloydb-password \
  --member="serviceAccount:${BACKEND_SA}@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor" || true

gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:${BACKEND_SA}@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/aiplatform.user" || true

# Cloud Build SA permissions for deployment
PROJECT_NUMBER=$(gcloud projects describe "$PROJECT_ID" --format="value(projectNumber)")
CB_SA="${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com"

gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:${CB_SA}" \
  --role="roles/run.admin" || true

gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:${CB_SA}" \
  --role="roles/iam.serviceAccountUser" || true

gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:${CB_SA}" \
  --role="roles/secretmanager.secretAccessor" || true

# ------------------------------------------------------------------------------
# Step 9: Instructions for Cloud Build GitHub Connection
# ------------------------------------------------------------------------------
echo ""
echo "================================================================================"
echo "  Infrastructure Setup Complete!"
echo "================================================================================"
echo "AlloyDB Private IP:   $ALLOYDB_IP"
echo "AlloyDB Password:     Stored securely in Secret Manager ('alloydb-password')"
echo "To view your DB password anytime:"
echo "   gcloud secrets versions access latest --secret=\"alloydb-password\""
echo ""
echo "VPC Subnet:           $SUBNET_NAME in $VPC_NAME"
echo "Artifact Registry:    $REGION-docker.pkg.dev/$PROJECT_ID/$ARTIFACT_REPO"
echo ""
echo "To link your GitHub repository (https://github.com/EaseMyWorld/gh-wm-coach) to Cloud Build:"
echo "1. Connect GitHub repo in Cloud Build Console:"
echo "   https://console.cloud.google.com/cloud-build/triggers/connect?project=$PROJECT_ID"
echo ""
echo "2. Create the Trigger via gcloud CLI:"
echo "   gcloud builds triggers create github \\"
echo "     --name=\"deploy-gh-wm-coach-on-push\" \\"
echo "     --repo-owner=\"EaseMyWorld\" \\"
echo "     --repo-name=\"gh-wm-coach\" \\"
echo "     --branch-pattern=\"^main$\" \\"
echo "     --build-config=\"cloudbuild.yaml\" \\"
echo "     --substitutions=_ALLOYDB_IP=\"$ALLOYDB_IP\",_REGION=\"$REGION\""
echo ""
echo "Or trigger an immediate one-off deployment right now using:"
echo "   ./scripts/deploy.sh"
echo "================================================================================"
