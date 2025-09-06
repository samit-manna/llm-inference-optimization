locals {
  project_number = data.google_project.project.number
}

data "google_project" "project" {}

# Enable required APIs
resource "google_project_service" "services" {
  for_each = toset([
    "aiplatform.googleapis.com",
    "artifactregistry.googleapis.com",
    "compute.googleapis.com"
  ])
  project = var.project_id
  service = each.key
}

# Artifact Registry repository (Docker)
resource "google_artifact_registry_repository" "repo" {
  location      = var.region
  repository_id = var.gar_repo
  description   = "LLM serving images"
  format        = "DOCKER"
  depends_on    = [google_project_service.services]
}

# Service Account for deployment ops
resource "google_service_account" "deployer" {
  account_id   = var.service_account_name
  display_name = "Vertex Deployer"
}

# Grant the deployer broad but scoped roles (tune per your org policy)
resource "google_project_iam_member" "deployer_aiplatform_admin" {
  project = var.project_id
  role    = "roles/aiplatform.admin"
  member  = "serviceAccount:${google_service_account.deployer.email}"
}

# Let Vertex AI service agent pull images from GAR

# Vertex AI service agent email pattern: service-${project_number}@gcp-sa-aiplatform.iam.gserviceaccount.com
resource "google_project_iam_member" "aiplatform_sa_gar_reader" {
  project = var.project_id
  role    = "roles/artifactregistry.reader"
  member  = "serviceAccount:service-${local.project_number}@gcp-sa-aiplatform.iam.gserviceaccount.com"
  depends_on = [google_project_service.services, google_artifact_registry_repository.repo]
}

# Create the Endpoint resource in Vertex AI
resource "google_vertex_ai_endpoint" "endpoint" {
  name         = var.endpoint_name
  provider     = google-beta
  display_name = var.endpoint_display_name
  location     = var.region
  description  = "vLLM on L4 (Terraform-managed)"
  depends_on   = [google_project_service.services]
}
