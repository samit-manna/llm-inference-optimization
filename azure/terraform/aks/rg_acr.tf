resource "azurerm_resource_group" "rg" {
  name     = "${var.name}-${var.rg_name}"
  location = var.location
}

resource "azurerm_container_registry" "acr" {
  name                = "${var.name}${var.acr_name}"
  resource_group_name = azurerm_resource_group.rg.name
  location            = var.location
  sku                 = "Premium"
  admin_enabled       = false
}

resource "azurerm_role_assignment" "aks_acr_pull" {
  scope                = azurerm_container_registry.acr.id
  role_definition_name = "AcrPull"
  principal_id         = azurerm_kubernetes_cluster.aks.identity[0].principal_id
}

# Explicit ACR attachment to AKS for better integration
resource "null_resource" "attach_acr_to_aks" {
  depends_on = [
    azurerm_kubernetes_cluster.aks,
    azurerm_container_registry.acr,
    azurerm_role_assignment.aks_acr_pull
  ]

  provisioner "local-exec" {
    command = "az aks update --name ${azurerm_kubernetes_cluster.aks.name} --resource-group ${azurerm_resource_group.rg.name} --attach-acr ${azurerm_container_registry.acr.name}"
  }

  # Trigger re-run if ACR or AKS changes
  triggers = {
    aks_id = azurerm_kubernetes_cluster.aks.id
    acr_id = azurerm_container_registry.acr.id
  }
}
