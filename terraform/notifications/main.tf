resource "aws_ecr_repository_policy" "lambda" {
  repository = var.repository_name
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
      Action    = ["ecr:BatchGetImage", "ecr:GetDownloadUrlForLayer"]
    }]
  })
}

resource "aws_cloudwatch_log_group" "worker" {
  name              = "/aws/lambda/${var.name}"
  retention_in_days = 14
}

resource "aws_lambda_function" "worker" {
  function_name = var.name
  package_type  = "Image"
  image_uri     = "${var.repository_url}@${var.config.image_digest}"
  architectures = ["x86_64"]
  role          = aws_iam_role.worker.arn
  memory_size   = 512
  timeout       = 30

  vpc_config {
    subnet_ids         = var.subnet_ids
    security_group_ids = [var.worker_security_group]
  }

  environment {
    variables = {
      DATABASE_SECRET_ARN = var.config.database_secret_arn
      PGSSLROOTCERT       = "/var/task/rds-global-bundle.pem"
      PGSSLMODE           = "verify-full"
      PGCONNECT_TIMEOUT   = "5"
    }
  }

  depends_on = [
    aws_ecr_repository_policy.lambda,
    aws_cloudwatch_log_group.worker,
    aws_iam_role_policy.worker,
    aws_vpc_endpoint.private,
  ]
}

resource "aws_lambda_event_source_mapping" "broker" {
  event_source_arn = var.broker_arn
  function_name    = aws_lambda_function.worker.arn
  queues           = ["notifications"]
  batch_size       = 10
  enabled          = var.config.enabled

  source_access_configuration {
    type = "BASIC_AUTH"
    uri  = var.config.broker_secret_arn
  }

  source_access_configuration {
    type = "VIRTUAL_HOST"
    uri  = "/"
  }

  depends_on = [
    aws_vpc_security_group_ingress_rule.endpoint,
    aws_vpc_security_group_egress_rule.endpoint,
  ]
}
