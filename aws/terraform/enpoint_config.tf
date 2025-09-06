resource "aws_sagemaker_endpoint_configuration" "cfg" {
  name = "${var.name}-cfg"

  production_variants {
    variant_name           = "AllTraffic"
    model_name             = aws_sagemaker_model.vllm.name
    initial_instance_count = 1
    instance_type          = "ml.g5.2xlarge"
    initial_variant_weight = 1.0
  }
}
