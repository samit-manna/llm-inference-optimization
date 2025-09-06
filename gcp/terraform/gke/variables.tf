variable "project_id" {
  type = string
}
variable "region" {
  type    = string
  default = "us-east1"
}
variable "zone" {
  type    = string
  default = "us-east1-c"
}

variable "cluster_name" {
  type    = string
  default = "llm-gke"
}
variable "network" {
  type    = string
  default = "default"
}
variable "subnetwork" {
  type    = string
  default = "default"
}

# Node pool sizing
variable "np_name" {
  type    = string
  default = "gpu-pool"
}
variable "machine_type" {
  type    = string
  default = "g2-standard-8"
}
variable "gpu_type" {
  type    = string
  default = "nvidia-l4"
}
variable "gpu_count" {
  type    = number
  default = 1
}
variable "disk_size_gb" {
  type    = number
  default = 200
}
variable "min_nodes" {
  type    = number
  default = 1
}
variable "max_nodes" {
  type    = number
  default = 2
}

# Artifact Registry repo name
variable "gar_repo" {
  type    = string
  default = "llm-images"
}

# Image registry for vLLM container
variable "image_uri" {
  type        = string
  description = "GAR image, e.g. us-east1-docker.pkg.dev/PROJECT/REPO/vllm-serve:v1"
}

# Model/runtime env
variable "model_id" {
  type    = string
  default = "hugging-quants/Meta-Llama-3.1-8B-Instruct-AWQ-INT4"
}
variable "max_model_len" {
  type    = number
  default = 4096
}
variable "gpu_mem_util" {
  type    = number
  default = 0.95
}
variable "max_batch_total_tokens" {
  type    = number
  default = 16384
}
variable "hf_token" {
  type    = string
  default = ""
}

