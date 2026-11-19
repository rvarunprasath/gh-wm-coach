# ==============================================================================
# Terraform Infrastructure as Code for GH Wealth Management AI Coach
# - VPC Network with Direct VPC Egress Subnet
# - Private Service Access (PSA) peering for AlloyDB
# - AlloyDB for PostgreSQL Cluster & Primary Instance
# - Secret Manager (Gemini API Key, AlloyDB Password)
# - Artifact Registry Docker Repository
# - Cloud Run v2 Backend (FastAPI + AlloyDB + Gemini)
# - Cloud Run v2 Frontend (Next.js)
# - Cloud Build Triggers for https://github.com/EaseMyWorld/gh-wm-coach
# ==============================================================================

terraform {
  required_version = ">= 1.5.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.30"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = "~> 5.30"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

provider "google-beta" {
  project = var.project_id
  region  = var.region
}

# ------------------------------------------------------------------------------
# 1. Enable Required Google Cloud APIs
# ------------------------------------------------------------------------------
locals {
  gcp_services = [
    "run.googleapis.com",
    "compute.googleapis.com",
    "servicenetworking.googleapis.com",
    "alloydb.googleapis.com",
    "cloudbuild.googleapis.com",
    "artifactregistry.googleapis.com",
    "secretmanager.googleapis.com",
    "aiplatform.googleapis.com",
    "iam.googleapis.com"
  ]
}

resource "google_project_service" "services" {
  for_each           = toset(locals.gcp_services)
  project            = var.project_id
  service            = each.key
  disable_on_destroy = false
}

# ------------------------------------------------------------------------------
# 2. VPC Network & Cloud Run Direct VPC Egress Subnet
# ------------------------------------------------------------------------------
resource "google_compute_network" "vpc" {
  name                    = var.vpc_name
  auto_create_subnetworks = false
  depends_on              = [google_project_service.services]
}

resource "google_compute_subnetwork" "subnet" {
  name                     = var.subnet_name
  ip_cidr_range            = var.subnet_cidr
  region                   = var.region
  network                  = google_compute_network.vpc.id
  private_ip_google_access = true
}

# ------------------------------------------------------------------------------
# 3. Private Services Access (PSA) for AlloyDB Private IP Peering
# ------------------------------------------------------------------------------
resource "google_compute_global_address" "private_ip_alloc" {
  name          = "alloydb-psa-range-${var.vpc_name}"
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = 16
  network       = google_compute_network.vpc.id
}

resource "google_service_networking_connection" "private_vpc_connection" {
  network                 = google_compute_network.vpc.id
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.private_ip_alloc.name]
}

# ------------------------------------------------------------------------------
# 4. Artifact Registry Repository
# ------------------------------------------------------------------------------
resource "google_artifact_registry_repository" "repo" {
  location      = var.region
  repository_id = var.artifact_repo_name
  description   = "Docker repository for GH Wealth Management Coach containers"
  format        = "DOCKER"
  depends_on    = [google_project_service.services]
}

# ------------------------------------------------------------------------------
# 5. Secret Manager (Placeholders / Configured Values)
# ------------------------------------------------------------------------------
resource "random_password" "auto_db_password" {
  length  = 20
  special = false
}

locals {
  effective_db_password = (var.db_password == "" || var.db_password == "YOUR_ALLOYDB_PASSWORD_HERE") ? random_password.auto_db_password.result : var.db_password
}

resource "google_secret_manager_secret" "gemini_key" {
  secret_id = "gemini-api-key"
  replication {
    auto {}
  }
  depends_on = [google_project_service.services]
}

resource "google_secret_manager_secret_version" "gemini_key_version" {
  secret      = google_secret_manager_secret.gemini_key.id
  secret_data = var.gemini_api_key
}

resource "google_secret_manager_secret" "db_password" {
  secret_id = "alloydb-password"
  replication {
    auto {}
  }
  depends_on = [google_project_service.services]
}

resource "google_secret_manager_secret_version" "db_password_version" {
  secret      = google_secret_manager_secret.db_password.id
  secret_data = local.effective_db_password
}

# ------------------------------------------------------------------------------
# 6. AlloyDB for PostgreSQL Cluster & Primary Instance
# ------------------------------------------------------------------------------
resource "google_alloydb_cluster" "cluster" {
  cluster_id = "wm-coach-alloydb-cluster"
  location   = var.region
  network_config {
    network = google_compute_network.vpc.id
  }
  initial_user {
    user     = "postgres"
    password = local.effective_db_password
  }
  depends_on = [
    google_service_networking_connection.private_vpc_connection,
    google_project_service.services
  ]
}

resource "google_alloydb_instance" "primary" {
  cluster       = google_alloydb_cluster.cluster.name
  instance_id   = "wm-coach-alloydb-primary"
  instance_type = "PRIMARY"
  machine_config {
    cpu_count = 2
  }
  availability_type = "ZONAL"
  depends_on        = [google_alloydb_cluster.cluster]
}

# ------------------------------------------------------------------------------
# 7. IAM Service Accounts
# ------------------------------------------------------------------------------
resource "google_service_account" "backend_sa" {
  account_id   = "wm-coach-backend-sa"
  display_name = "GH WM Coach Backend Service Account"
}

resource "google_service_account" "frontend_sa" {
  account_id   = "wm-coach-frontend-sa"
  display_name = "GH WM Coach Frontend Service Account"
}

# Grant Backend SA Secret Accessor on Secret Manager
resource "google_secret_manager_secret_iam_member" "backend_gemini_secret_access" {
  secret_id = google_secret_manager_secret.gemini_key.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.backend_sa.email}"
}

resource "google_secret_manager_secret_iam_member" "backend_db_secret_access" {
  secret_id = google_secret_manager_secret.db_password.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.backend_sa.email}"
}

# Grant Vertex AI user role in case Vertex AI is used for Gemini
resource "google_project_iam_member" "backend_vertex_access" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.backend_sa.email}"
}

# Grant Cloud Build SA permissions to deploy to Cloud Run & act as Service Accounts
data "google_project" "project" {}

resource "google_project_iam_member" "cloudbuild_run_admin" {
  project = var.project_id
  role    = "roles/run.admin"
  member  = "serviceAccount:${data.google_project.project.number}@cloudbuild.gserviceaccount.com"
}

resource "google_project_iam_member" "cloudbuild_sa_user" {
  project = var.project_id
  role    = "roles/iam.serviceAccountUser"
  member  = "serviceAccount:${data.google_project.project.number}@cloudbuild.gserviceaccount.com"
}

resource "google_project_iam_member" "cloudbuild_secret_accessor" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${data.google_project.project.number}@cloudbuild.gserviceaccount.com"
}

# ------------------------------------------------------------------------------
# 8. Cloud Run v2 Backend Service (Direct VPC Egress to AlloyDB)
# ------------------------------------------------------------------------------
resource "google_cloud_run_v2_service" "backend" {
  name     = "wm-coach-backend"
  location = var.region
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    service_account = google_service_account.backend_sa.email

    vpc_access {
      network_interfaces {
        network    = google_compute_network.vpc.id
        subnetwork = google_compute_subnetwork.subnet.id
      }
      egress = "PRIVATE_RANGES_ONLY"
    }

    containers {
      image = "${var.region}-docker.pkg.dev/${var.project_id}/${var.artifact_repo_name}/backend:latest"

      resources {
        limits = {
          cpu    = "1"
          memory = "1Gi"
        }
      }

      env {
        name  = "DB_HOST"
        value = google_alloydb_instance.primary.ip_address
      }
      env {
        name  = "DB_PORT"
        value = "5432"
      }
      env {
        name  = "DB_NAME"
        value = "financial_coach"
      }
      env {
        name  = "DB_USER"
        value = "postgres"
      }
      env {
        name  = "GEMINI_MODEL"
        value = "gemini-2.0-flash"
      }

      env {
        name = "DB_PASSWORD"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.db_password.secret_id
            version = "latest"
          }
        }
      }

      env {
        name = "GEMINI_API_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.gemini_key.secret_id
            version = "latest"
          }
        }
      }
    }
  }

  depends_on = [
    google_alloydb_instance.primary,
    google_secret_manager_secret_version.gemini_key_version,
    google_secret_manager_secret_version.db_password_version
  ]
}

# Allow unauthenticated invocations for backend API (or internal via load balancer/frontend)
resource "google_cloud_run_v2_service_iam_member" "backend_public_access" {
  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_service.backend.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# ------------------------------------------------------------------------------
# 9. Cloud Run v2 Frontend Service (Direct VPC Egress to Backend / Cloud Run)
# ------------------------------------------------------------------------------
resource "google_cloud_run_v2_service" "frontend" {
  name     = "wm-coach-frontend"
  location = var.region
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    service_account = google_service_account.frontend_sa.email

    vpc_access {
      network_interfaces {
        network    = google_compute_network.vpc.id
        subnetwork = google_compute_subnetwork.subnet.id
      }
      egress = "PRIVATE_RANGES_ONLY"
    }

    containers {
      image = "${var.region}-docker.pkg.dev/${var.project_id}/${var.artifact_repo_name}/frontend:latest"

      resources {
        limits = {
          cpu    = "1"
          memory = "1Gi"
        }
      }

      env {
        name  = "BACKEND_URL"
        value = google_cloud_run_v2_service.backend.uri
      }
      env {
        name  = "NODE_ENV"
        value = "production"
      }
    }
  }

  depends_on = [google_cloud_run_v2_service.backend]
}

# Allow unauthenticated public access for Frontend UI
resource "google_cloud_run_v2_service_iam_member" "frontend_public_access" {
  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_service.frontend.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# ------------------------------------------------------------------------------
# 10. Cloud Build GitHub Trigger (https://github.com/EaseMyWorld/gh-wm-coach)
# ------------------------------------------------------------------------------
resource "google_cloudbuild_trigger" "github_push_trigger" {
  name        = "deploy-gh-wm-coach-on-push"
  description = "Continuous Deployment pipeline from https://github.com/EaseMyWorld/gh-wm-coach"
  filename    = "cloudbuild.yaml"

  github {
    owner = var.github_repo_owner
    name  = var.github_repo_name
    push {
      branch = var.github_branch
    }
  }

  substitutions = {
    _REGION                = var.region
    _ARTIFACT_REPO         = var.artifact_repo_name
    _VPC_NETWORK           = var.vpc_name
    _VPC_SUBNET            = var.subnet_name
    _ALLOYDB_IP            = google_alloydb_instance.primary.ip_address
    _GEMINI_KEY_SECRET     = google_secret_manager_secret.gemini_key.secret_id
    _DB_PASSWORD_SECRET    = google_secret_manager_secret.db_password.secret_id
    _BACKEND_SERVICE_NAME  = "wm-coach-backend"
    _FRONTEND_SERVICE_NAME = "wm-coach-frontend"
  }

  depends_on = [
    google_alloydb_instance.primary,
    google_artifact_registry_repository.repo
  ]
}
