data "aws_iam_policy_document" "sm_exec" {
  statement {
    actions = [
      "logs:CreateLogGroup","logs:CreateLogStream","logs:PutLogEvents",
      "cloudwatch:PutMetricData","cloudwatch:GetMetricData","cloudwatch:ListMetrics",
      "s3:GetObject","s3:ListBucket","s3:PutObject"
    ]
    resources = ["*"]
  }
}
resource "aws_iam_role" "sagemaker_exec" {
  name               = "${var.name}-sm-exec"
  assume_role_policy = jsonencode({
    Version="2012-10-17",
    Statement=[{Effect="Allow", Principal={Service="sagemaker.amazonaws.com"}, Action="sts:AssumeRole"}]
  })
}
resource "aws_iam_role_policy" "sagemaker_exec" {
  role   = aws_iam_role.sagemaker_exec.id
  policy = data.aws_iam_policy_document.sm_exec.json
}

# iam.tf (add this)
resource "aws_iam_role_policy_attachment" "sm_ecr_readonly" {
  role       = aws_iam_role.sagemaker_exec.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
}

# Wait for IAM role to propagate
resource "time_sleep" "wait_for_iam_role" {
  depends_on = [
    aws_iam_role.sagemaker_exec,
    aws_iam_role_policy.sagemaker_exec,
    aws_iam_role_policy_attachment.sm_ecr_readonly
  ]

  create_duration = "30s"
}

