variable "name" {
  description = "Project name prefix"
  type        = string
  default     = "sam"
}

variable "hostname" {
  description = "Hostname for the VLLM service"
  type        = string
}

variable "hf_token" {
  description = "Hugging Face token for model access"
  type        = string
  sensitive   = true
}

variable "vllm_image" {
  description = "Docker image for the VLLM"
  type        = string
  default     = "vllm/vllm-openai:v0.5.4"
}

variable "proxy_image" {
  description = "Docker image for the VLLM proxy"
  type        = string
}

variable "instance_hourly_usd" {
  description = "Hourly cost in USD for the instance"
  type        = number
  default    = 1.18
}

# KEDA / Prom settings
variable "prom_server" {
  type        = string
  description = "Prometheus server address for KEDA Prom trigger"
  default     = "http://prometheus-operated.monitoring.svc:9090"
}

variable "tokens_per_min_threshold" {
  type        = number
  description = "Scale-out threshold (CompletionTokens/min)"
  default     = 42000
}

variable "create_custom_resources" {
  type        = bool
  description = "Whether to create custom resources that depend on CRDs (Gateway, KEDA, ServiceMonitor)"
  default     = false
}
