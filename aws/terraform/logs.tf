resource "aws_cloudwatch_log_group" "sagemaker" {
  name              = "/aws/sagemaker/llm-vllm"
  retention_in_days = 30
}
