resource "azurerm_kubernetes_cluster_node_pool" "gpu" {
  name                  = "gpu"
  kubernetes_cluster_id = azurerm_kubernetes_cluster.aks.id
  vm_size               = var.gpu_vm_size
  mode                  = "User"
  os_disk_size_gb       = 200
  orchestrator_version  = azurerm_kubernetes_cluster.aks.kubernetes_version
  node_labels = { "sku" = "gpu" }
  node_taints = ["sku=gpu:NoSchedule"]
  
  # GPU driver configuration
  gpu_driver = "Install"

  # Node auto-scaling
  auto_scaling_enabled   = true
  node_count            = 1
  min_count             = 1
  max_count             = 4

  temporary_name_for_rotation = "gpupooltmp"

  upgrade_settings {
    drain_timeout_in_minutes = 0
    max_surge = "10%"
    node_soak_duration_in_minutes = 0
  }
}
