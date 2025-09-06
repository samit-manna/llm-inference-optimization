terraform {
  required_version = ">= 1.6"
  required_providers {
    aws = { source = "hashicorp/aws", version = ">= 5.50" }
    time = { source = "hashicorp/time", version = ">= 0.9" }
  }
}
provider "aws" { region = var.region }