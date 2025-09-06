# outputs.tf
output "endpoint_name" {
  value = aws_sagemaker_endpoint.ep.name
}

output "region" {
  value = var.region
}

output "invocation_command" {
  value = <<EOF
aws sagemaker-runtime invoke-endpoint \\
  --endpoint-name ${aws_sagemaker_endpoint.ep.name} \\
  --body '{"prompt": "Explain LLM quantization", "max_tokens": 64}' \\
  --content-type "application/json" \\
  response.json
EOF
}

output "bench_url" {
  value       = "${aws_apigatewayv2_api.bench_api.api_endpoint}/v1/chat/completions"
  description = "Public HTTPS URL for benchmark proxy"
}