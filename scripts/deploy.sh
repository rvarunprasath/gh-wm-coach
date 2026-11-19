#!/usr/bin/env bash
# ==============================================================================
# GH Wealth Management AI Coach - Cloud Build Deployment Trigger
# Builds and deploys backend and frontend services to Cloud Run
# ==============================================================================
set -euo pipefail

PROJECT_ID="${PROJECT_ID:-artha-ai-wealth-coach}"
REGION="${REGION:-us-central1}"
ALLOYDB_CLUSTER="${ALLOYDB_CLUSTER:-wm-coach-alloydb-cluster}"
ALLOYDB_INSTANCE="${ALLOYDB_INSTANCE:-wm-coach-alloydb-primary}"

if [ -z "$PROJECT_ID" ]; then
  echo "Error: PROJECT_ID is not set. Set it with: export PROJECT_ID=\"your-gcp-project-id\""
  exit 1
fi

echo "Resolving AlloyDB Instance Private IP in $REGION..."
ALLOYDB_IP=$(gcloud alloydb instances describe "$ALLOYDB_INSTANCE" \
  --cluster="$ALLOYDB_CLUSTER" \
  --region="$REGION" \
  --format="value(ipAddress)" 2>/dev/null || echo "10.10.0.3")

echo "Submitting build to Google Cloud Build using cloudbuild.yaml..."
echo "Project:     $PROJECT_ID"
echo "Region:      $REGION"
echo "AlloyDB IP:  $ALLOYDB_IP"
echo ""

gcloud builds submit \
  --config=cloudbuild.yaml \
  --substitutions=_REGION="$REGION",_ALLOYDB_IP="$ALLOYDB_IP" \
  .

echo "Deployment complete! Fetching service URLs:"
echo "Backend URL:  $(gcloud run services describe wm-coach-backend --region="$REGION" --format='value(status.url)')"
echo "Frontend URL: $(gcloud run services describe wm-coach-frontend --region="$REGION" --format='value(status.url)')"
