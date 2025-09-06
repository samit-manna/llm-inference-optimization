output "kube_config" {
  description = "Kubernetes configuration file contents"
  value = azurerm_kubernetes_cluster.aks.kube_config_raw
  sensitive = true
}

output "kube_config_base64" {
  description = "Base64 encoded Kubernetes configuration"
  value = base64encode(azurerm_kubernetes_cluster.aks.kube_config_raw)
  sensitive = true
}

# Structured kube config for Terraform providers
output "kube_config_data" {
  description = "Structured Kubernetes configuration data for providers"
  value = azurerm_kubernetes_cluster.aks.kube_config[0]
  sensitive = true
}

output "host" {
  description = "Kubernetes API server host"
  value = azurerm_kubernetes_cluster.aks.kube_config[0].host
  sensitive = true
}

output "client_certificate" {
  description = "Kubernetes client certificate"
  value = azurerm_kubernetes_cluster.aks.kube_config[0].client_certificate
  sensitive = true
}

output "client_key" {
  description = "Kubernetes client key"
  value = azurerm_kubernetes_cluster.aks.kube_config[0].client_key
  sensitive = true
}

output "cluster_ca_certificate" {
  description = "Kubernetes cluster CA certificate"
  value = azurerm_kubernetes_cluster.aks.kube_config[0].cluster_ca_certificate
  sensitive = true
}

output "cluster_name" {
  description = "AKS cluster name"
  value = azurerm_kubernetes_cluster.aks.name
}

output "resource_group_name" {
  description = "Resource group name"
  value = azurerm_resource_group.rg.name
}

# For Azure CLI commands
output "get_credentials_command" {
  description = "Azure CLI command to get AKS credentials"
  value = "az aks get-credentials --resource-group ${azurerm_resource_group.rg.name} --name ${azurerm_kubernetes_cluster.aks.name}"
}
