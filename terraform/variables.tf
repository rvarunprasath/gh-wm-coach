variable "project_id" {
  description = "Google Cloud Project ID where resources will be provisioned."
  type        = string
}

variable "region" {
  description = "Google Cloud region for resources (e.g. us-central1, us-east4, asia-south1)."
  type        = string
  default     = "us-central1"
}

variable "vpc_name" {
  description = "Name of the custom VPC network."
  type        = string
  default     = "wm-coach-vpc"
}

variable "subnet_name" {
  description = "Name of the subnet for Cloud Run Direct VPC Egress."
  type        = string
  default     = "wm-coach-subnet"
}

variable "subnet_cidr" {
  description = "CIDR block for the Cloud Run subnet."
  type        = string
  default     = "10.0.0.0/24"
}

variable "artifact_repo_name" {
  description = "Name of Artifact Registry Docker repository."
  type        = string
  default     = "wm-coach-repo"
}

variable "gemini_api_key" {
  description = "Google Gemini AI Studio API key (leave placeholder if using Vertex AI or configuring later)."
  type        = string
  default     = "YOUR_GEMINI_API_KEY_HERE"
  sensitive   = true
}

variable "db_password" {
  description = "Master password for AlloyDB for PostgreSQL postgres user."
  type        = string
  default     = "YOUR_ALLOYDB_PASSWORD_HERE"
  sensitive   = true
}

variable "github_repo_owner" {
  description = "GitHub repository owner."
  type        = string
  default     = "EaseMyWorld"
}

variable "github_repo_name" {
  description = "GitHub repository name."
  type        = string
  default     = "gh-wm-coach"
}

variable "github_branch" {
  description = "Branch name to trigger Cloud Build deployments on push."
  type        = string
  default     = "^main$"
}
