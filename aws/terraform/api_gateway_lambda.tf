# IAM for Lambda
resource "aws_iam_role" "bench_lambda_role" {
  name = "${var.name}-bench-lambda-role"
  assume_role_policy = jsonencode({
    Version="2012-10-17",
    Statement=[{
      Effect="Allow", Principal={ Service="lambda.amazonaws.com" }, Action="sts:AssumeRole"
    }]
  })
}

data "aws_caller_identity" "me" {}

data "aws_iam_policy_document" "bench_lambda_policy" {
  statement {
    actions   = ["logs:CreateLogGroup","logs:CreateLogStream","logs:PutLogEvents","cloudwatch:PutMetricData"]
    resources = ["*"]
  }
  statement {
    actions = ["sagemaker:InvokeEndpoint","sagemaker:InvokeEndpointAsync","sagemaker:InvokeEndpointWithResponseStream"]
    resources = ["arn:aws:sagemaker:${var.region}:${data.aws_caller_identity.me.account_id}:endpoint/${aws_sagemaker_endpoint.ep.name}"]
  }
}

resource "aws_iam_role_policy" "bench_lambda_policy" {
  role   = aws_iam_role.bench_lambda_role.id
  policy = data.aws_iam_policy_document.bench_lambda_policy.json
}

# Lambda function (zip from local file)
resource "aws_lambda_function" "bench_proxy" {
  function_name = "${var.name}-bench-proxy"
  role          = aws_iam_role.bench_lambda_role.arn
  handler       = "app.handler"
  runtime       = "python3.12"
  timeout       = 30
  memory_size   = 512
  filename      = "scripts/lambda_bench_proxy.zip"

  environment {
    variables = {
      ENDPOINT_NAME = "${aws_sagemaker_endpoint.ep.name}"
      REGION    = "${var.region}"
      INSTANCE_HOURLY_USD  = "1.21"  # <-- set to your region's ml.g5.2xlarge hourly price
      SM_INSTANCE_TYPE     = "ml.g5.2xlarge"
    }
  }
}

# API Gateway (HTTP API)
resource "aws_apigatewayv2_api" "bench_api" {
  name          = "${var.name}-bench-api"
  protocol_type = "HTTP"
}

resource "aws_apigatewayv2_integration" "bench_integration" {
  api_id           = aws_apigatewayv2_api.bench_api.id
  integration_type = "AWS_PROXY"
  integration_uri  = aws_lambda_function.bench_proxy.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "bench_route" {
  api_id    = aws_apigatewayv2_api.bench_api.id
  route_key = "POST /v1/chat/completions"
  target    = "integrations/${aws_apigatewayv2_integration.bench_integration.id}"
}

resource "aws_lambda_permission" "allow_apigw" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.bench_proxy.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.bench_api.execution_arn}/*/*"
}

resource "aws_apigatewayv2_stage" "bench_stage" {
  api_id      = aws_apigatewayv2_api.bench_api.id
  name        = "$default"
  auto_deploy = true
}
