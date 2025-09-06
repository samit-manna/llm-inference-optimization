variable "name" {
    description = "Resource name"
    type        = string
    default     = "samllm"
}

variable "region" {
    description = "The AWS region to deploy resources in"
    type        = string
    default     = "us-east-1"
}

# Use the official LMI container (v15). Replace with the correct region URI (example below).
# See the LMI blog/doc for the latest image tags per region.
# e.g., 763104351884.dkr.ecr.<region>.amazonaws.com/djl-inference:0.33.0-lmi15.0.0-cu128
variable "lmi_image_uri" {
    description = "Amazon-provided Large Model Inference (LMI) container image URI for the region"
    type = string
    default = "763104351884.dkr.ecr.us-east-1.amazonaws.com/djl-inference:0.33.0-lmi15.0.0-cu128"
}

variable "hf_token" {
  description = "Hugging Face token with access to the model repo"
  type        = string
  sensitive   = true
  default     = ""
}
