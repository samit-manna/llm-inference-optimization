# Enable required APIs
resource "google_project_service" "services" {
  for_each = toset([
    "container.googleapis.com",
    "compute.googleapis.com",
    "artifactregistry.googleapis.com",
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

# Service account for GKE nodes
resource "google_service_account" "gke_node_sa" {
  account_id   = "gke-node-sa"
  display_name = "GKE Node Service Account"
}

# IAM binding for Artifact Registry Reader
resource "google_project_iam_member" "gke_artifact_registry_reader" {
  project = var.project_id
  role    = "roles/artifactregistry.reader"
  member  = "serviceAccount:${google_service_account.gke_node_sa.email}"
}

# IAM binding for Container Registry Reader (for backward compatibility)
resource "google_project_iam_member" "gke_storage_object_viewer" {
  project = var.project_id
  role    = "roles/storage.objectViewer"
  member  = "serviceAccount:${google_service_account.gke_node_sa.email}"
}

# GKE cluster (Standard)
resource "google_container_cluster" "cluster" {
  name     = var.cluster_name
  location = var.zone
  network    = var.network
  subnetwork = var.subnetwork

  remove_default_node_pool = false
  initial_node_count       = 1
  deletion_protection      = false

  # Enable GKE-managed GPU drivers
  enable_kubernetes_alpha = false
  datapath_provider       = "ADVANCED_DATAPATH"

  # Use custom service account for cluster operations
  node_config {
    service_account = google_service_account.gke_node_sa.email
    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform"
    ]
  }

  workload_identity_config {
    workload_pool = "${var.project_id}.svc.id.goog"
  }

  # Autopilot = false (Standard)
}

# GPU node pool (L4)
resource "google_container_node_pool" "gpu_pool" {
  name       = var.np_name
  cluster    = google_container_cluster.cluster.name
  location   = var.zone

  node_count = var.min_nodes

  autoscaling {
    min_node_count = var.min_nodes
    max_node_count = var.max_nodes
  }

  node_config {
    machine_type = var.machine_type
    disk_size_gb = var.disk_size_gb
    image_type   = "COS_CONTAINERD"

    # Use custom service account with Artifact Registry permissions
    service_account = google_service_account.gke_node_sa.email

    guest_accelerator {
      type  = var.gpu_type
      count = var.gpu_count
    }

    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform"
    ]
    labels = {
      gpu = "l4"
    }
    taint {
      key    = "nvidia.com/gpu"
      value  = "present"
      effect = "NO_SCHEDULE"
    }
  }

  management {
    auto_repair  = true
    auto_upgrade = true
  }

  depends_on = [google_project_service.services, google_container_cluster.cluster]
}
