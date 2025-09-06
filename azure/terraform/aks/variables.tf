variable "subscription_id" {}
variable "name" {}
variable "location"   { default = "eastus" }
variable "rg_name"    { default = "rg-llm-aks" }
variable "acr_name"   { default = "llmacr1234" } # must be globally unique
variable "aks_name"   { default = "aks-llm" }
variable "kubernetes_version" { default = "1.29.7" } # adjust to your policy
variable "gpu_vm_size" { default = "Standard_NC4as_T4_v3" } # 1x T4, 4 vCPUs, 28GB RAM
# Available GPU VM sizes:
# Standard_NC4as_T4_v3      - 4 vCPUs, 28GB RAM, 1x T4 (lowest cost)
# Standard_NC6s_v3          - 6 vCPUs, 112GB RAM, 1x V100 (good balance)  
# Standard_NC8as_T4_v3      - 8 vCPUs, 56GB RAM, 1x T4 (better for VLLM)
# Standard_NV36adms_A10_v5  - 36 vCPUs, 440GB RAM, 1x A10 (best performance)
