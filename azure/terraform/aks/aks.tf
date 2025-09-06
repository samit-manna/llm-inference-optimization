resource "azurerm_kubernetes_cluster" "aks" {
  name                = "${var.name}-${var.aks_name}"
  location            = var.location
  resource_group_name = azurerm_resource_group.rg.name
  dns_prefix          = "${var.name}-${var.aks_name}-dns"

  default_node_pool {
    name       = "system"
    node_count = 1
    vm_size    = "Standard_D4s_v6"
    os_disk_size_gb = 100
    type       = "VirtualMachineScaleSets"
  }

  identity { type = "SystemAssigned" }

  network_profile {
    network_plugin = "azure"
    load_balancer_sku = "standard"
  }

  sku_tier = "Standard"
}
