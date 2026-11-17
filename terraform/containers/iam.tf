resource "aws_iam_role" "execution" {
  for_each = var.repositories

  name_prefix = "ecs-${each.key}-"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "ecs-tasks.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })

  tags = { Name = "${var.name}-${each.key}-execution" }
}

resource "aws_iam_role_policy" "execution" {
  for_each = var.repositories

  name = "ecs-execution"
  role = aws_iam_role.execution[each.key].name
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = concat(
      [
        {
          Effect   = "Allow"
          Action   = ["ecr:GetAuthorizationToken"]
          Resource = ["*"]
        },
        {
          Effect   = "Allow"
          Action   = ["ecr:BatchGetImage", "ecr:GetDownloadUrlForLayer", "ecr:BatchCheckLayerAvailability"]
          Resource = [each.value.arn]
        },
        {
          Effect   = "Allow"
          Action   = ["logs:CreateLogStream", "logs:PutLogEvents"]
          Resource = ["${trimsuffix(aws_cloudwatch_log_group.service[each.key].arn, ":*")}:log-stream:*"]
        }
      ],
      each.key == "itinerary" ? [{
        Effect   = "Allow"
        Action   = ["secretsmanager:GetSecretValue"]
        Resource = values(local.itinerary_secrets)
      }] : [],
      each.key == "itinerary" && length(var.config.secrets_kms_key_arns) > 0 ? [{
        Effect   = "Allow"
        Action   = ["kms:Decrypt"]
        Resource = tolist(var.config.secrets_kms_key_arns)
      }] : []
    )
  })
}
