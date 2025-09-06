variable "project_id" { type = string }
variable "region" {
  type    = string
  default = "us-east1"
}

# Artifact Registry
variable "gar_repo" {
  type    = string
  default = "llm-infer"
}
variable "image_name" {
  type    = string
  default = "vllm-serve"
}
variable "image_tag" {
  type    = string
  default = "v1"
}
variable "image_uri" {
  type        = string
  description = "Full image URI including tag (e.g. us-east1-docker.pkg.dev/PROJECT/REPO/IMAGE:TAG)"
}

# Vertex naming
variable "endpoint_name" {
  type    = string
  default = "sam-vllm-endpoint"
}
variable "endpoint_display_name" {
  type    = string
  default = "vllm-l4-endpoint"
}
variable "model_display_name" {
  type    = string
  default = "vllm-l4-model"
}

# Compute config
variable "machine_type" {
  type    = string
  default = "g2-standard-8"
}
variable "accelerator_type" {
  type    = string
  default = "nvidia-l4"
}
variable "accelerator_count" {
  type    = number
  default = 1
}
variable "min_replica" {
  type    = number
  default = 1
}
variable "max_replica" {
  type    = number
  default = 2
}

# Container contract
variable "container_port" {
  type    = number
  default = 8080
}
variable "container_predict_route" {
  type    = string
  default = "/predict"
}
variable "container_health_route" {
  type    = string
  default = "/healthz"
}

# Runtime envs for the container (Vertex Model upload)
variable "container_env" {
  type = map(string)
  default = {
    MODEL_ID                    = "hugging-quants/Meta-Llama-3.1-8B-Instruct-AWQ-INT4"
    OPTION_MAX_MODEL_LEN        = "8192"
    OPTION_GPU_MEMORY_UTILIZATION = "0.95"
    OPTION_ENFORCE_EAGER        = "true"
    MAX_BATCH_TOTAL_TOKENS      = "32768"
    VLLM_PORT                   = "8000"
    PORT                        = "8080"
  }
}

# Service Account for deployment
variable "service_account_name" {
  type    = string
  default = "vertex-deployer"
}
