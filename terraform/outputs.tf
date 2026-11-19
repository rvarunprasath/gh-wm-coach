output "frontend_url" {
  description = "Public URL of the GH Wealth Management Coach Frontend UI"
  value       = google_cloud_run_v2_service.frontend.uri
}

output "backend_url" {
  description = "URL of the FastAPI Backend Service"
  value       = google_cloud_run_v2_service.backend.uri
}

output "alloydb_primary_private_ip" {
  description = "Private IP address of the AlloyDB Primary Instance"
  value       = google_alloydb_instance.primary.ip_address
}

output "vpc_network_name" {
  description = "Name of the custom VPC network"
  value       = google_compute_network.vpc.name
}

output "vpc_subnet_name" {
  description = "Name of the Direct VPC Egress subnet"
  value       = google_compute_subnetwork.subnet.name
}

output "artifact_registry_repository" {
  description = "Artifact Registry Docker repository endpoint"
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${var.artifact_repo_name}"
}

output "cloud_build_trigger_id" {
  description = "ID of the Cloud Build GitHub continuous deployment trigger"
  value       = google_cloudbuild_trigger.github_push_trigger.id
}
