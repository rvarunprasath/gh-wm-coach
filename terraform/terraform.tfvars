# ==============================================================================
# GH Wealth Management AI Coach - Terraform Configuration
# Project: artha-ai-wealth-coach
# ==============================================================================

# Google Cloud Project ID
project_id = "artha-ai-wealth-coach"

# Deployment Region (AlloyDB + Cloud Run + Artifact Registry)
region = "us-central1"

# Custom VPC Configuration for Direct VPC Egress
vpc_name    = "wm-coach-vpc"
subnet_name = "wm-coach-subnet"
subnet_cidr = "10.0.0.0/24"

# Artifact Registry Repository Name
artifact_repo_name = "wm-coach-repo"

# Google Gemini API Key (set your key from https://aistudio.google.com/ or keep placeholder)
gemini_api_key = "YOUR_GEMINI_API_KEY_HERE"

# Master password for AlloyDB for PostgreSQL
db_password = "test789$@$#"

# GitHub Continuous Deployment Configuration
github_repo_owner = "EaseMyWorld"
github_repo_name  = "gh-wm-coach"
github_branch     = "^(main|arun)$"
