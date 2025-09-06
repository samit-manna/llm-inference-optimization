resource "aws_sagemaker_endpoint" "ep" {
  name                 = "${var.name}-ep"
  endpoint_config_name = aws_sagemaker_endpoint_configuration.cfg.name
}
