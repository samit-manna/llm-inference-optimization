variable "subscription_id" {}
variable "name" {}
variable "location"   { default = "eastus" }
variable "rg_name"    { default = "rg-llm-aks" }
variable "acr_name"   { default = "llmacr1234" } # must be globally unique
variable "aks_name"   { default = "aks-llm" }
variable "kubernetes_version" { default = "1.29.7" } # adjust to your policy
variable "gpu_vm_size" { default = "Standard_NV36adms_A10_v5" } # 1x A10
