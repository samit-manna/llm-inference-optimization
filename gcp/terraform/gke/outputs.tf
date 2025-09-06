output "cluster_name" { value = google_container_cluster.cluster.name }
output "zone"         { value = var.zone }
output "np_name"      { value = google_container_node_pool.gpu_pool.name }
output "artifact_registry_url" { 
  value = "${var.region}-docker.pkg.dev/${var.project_id}/${var.gar_repo}"
  description = "Artifact Registry repository URL for Docker images"
}
