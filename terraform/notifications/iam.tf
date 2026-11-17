locals {
  secrets = [var.config.database_secret_arn, var.config.broker_secret_arn]
}

resource "aws_iam_role" "worker" {
  name_prefix = "notifications-"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy" "worker" {
  name = "notification-worker"
  role = aws_iam_role.worker.name
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = concat([
      {
        Effect   = "Allow"
        Action   = ["secretsmanager:GetSecretValue"]
        Resource = local.secrets
      },
      {
        Effect   = "Allow"
        Action   = ["mq:DescribeBroker"]
        Resource = [var.broker_arn]
      },
      {
        Effect   = "Allow"
        Action   = ["logs:CreateLogStream", "logs:PutLogEvents"]
        Resource = ["${trimsuffix(aws_cloudwatch_log_group.worker.arn, ":*")}:log-stream:*"]
      },
      {
        Effect = "Allow"
        Action = [
          "ec2:CreateNetworkInterface",
          "ec2:DeleteNetworkInterface",
          "ec2:DescribeNetworkInterfaces",
          "ec2:DescribeSecurityGroups",
          "ec2:DescribeSubnets",
          "ec2:DescribeVpcs",
          "ec2:AssignPrivateIpAddresses",
          "ec2:UnassignPrivateIpAddresses",
        ]
        Resource = "*"
      },
    ], length(var.config.secrets_kms_key_arns) == 0 ? [] : [{
      Effect   = "Allow"
      Action   = ["kms:Decrypt"]
      Resource = tolist(var.config.secrets_kms_key_arns)
    }])
  })
}
