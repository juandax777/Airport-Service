variable "github_actions" {
  description = "Repositorio y entorno para habilitar los roles OIDC. Null desactiva la integración."
  type = object({
    repository            = string
    environment           = string
    ecr_repository_prefix = string
    existing_provider_arn = optional(string)
  })
  default = null

  validation {
    condition = var.github_actions == null || try(
      can(regex("^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$", var.github_actions.repository)) &&
      can(regex("^[a-z0-9-]+$", var.github_actions.environment)),
      false
    )
    error_message = "Usa un repositorio owner/name y un entorno en minúsculas con guiones."
  }
}

locals {
  github_jobs = var.github_actions == null ? toset([]) : toset(["plan", "publish"])
  oidc_host   = "token.actions.githubusercontent.com"
  oidc_arn    = try(coalesce(var.github_actions.existing_provider_arn, aws_iam_openid_connect_provider.github[0].arn), null)
  state_key   = var.github_actions == null ? null : "${var.github_actions.environment}/terraform.tfstate"
  ecr_names   = ["web-app", "airport-service", "itinerary-service", "notification-service"]
}

resource "aws_iam_openid_connect_provider" "github" {
  count = var.github_actions != null && try(var.github_actions.existing_provider_arn == null, false) ? 1 : 0

  url            = "https://${local.oidc_host}"
  client_id_list = ["sts.amazonaws.com"]
}

resource "aws_iam_role" "github" {
  for_each = local.github_jobs

  name_prefix = "itineraries-${each.key}-"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Federated = local.oidc_arn }
      Action    = "sts:AssumeRoleWithWebIdentity"
      Condition = {
        StringEquals = {
          "${local.oidc_host}:aud" = "sts.amazonaws.com"
          "${local.oidc_host}:sub" = "repo:${var.github_actions.repository}:environment:${var.github_actions.environment}-${each.key}"
        }
      }
    }]
  })
}

resource "aws_iam_role_policy" "publish" {
  count = var.github_actions == null ? 0 : 1

  name = "publish-project-images"
  role = aws_iam_role.github["publish"].name
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = "ecr:GetAuthorizationToken"
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "ecr:BatchCheckLayerAvailability",
          "ecr:BatchGetImage",
          "ecr:CompleteLayerUpload",
          "ecr:DescribeImages",
          "ecr:InitiateLayerUpload",
          "ecr:PutImage",
          "ecr:UploadLayerPart",
        ]
        Resource = [
          for name in local.ecr_names :
          "arn:aws:ecr:${var.aws_region}:${var.aws_account_id}:repository/${var.github_actions.ecr_repository_prefix}/${name}"
        ]
      },
    ]
  })
}

resource "aws_iam_role_policy" "plan" {
  count = var.github_actions == null ? 0 : 1

  name = "plan-project-infrastructure"
  role = aws_iam_role.github["plan"].name
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = "s3:ListBucket"
        Resource = aws_s3_bucket.state.arn
        Condition = {
          StringEquals = { "s3:prefix" = [local.state_key, "env:/"] }
        }
      },
      {
        Effect   = "Allow"
        Action   = "s3:GetObject"
        Resource = "${aws_s3_bucket.state.arn}/${local.state_key}"
      },
      {
        Effect   = "Allow"
        Action   = ["s3:GetObject", "s3:PutObject", "s3:DeleteObject"]
        Resource = "${aws_s3_bucket.state.arn}/${local.state_key}.tflock"
      },
      {
        Effect = "Allow"
        Action = [
          "lambda:GetFunction",
          "lambda:GetFunctionConcurrency",
          "lambda:GetFunctionCodeSigningConfig",
          "lambda:GetRuntimeManagementConfig",
          "lambda:ListTags",
        ]
        Resource = "arn:aws:lambda:${var.aws_region}:${var.aws_account_id}:function:${var.github_actions.ecr_repository_prefix}-notifications"
      },
      {
        Effect = "Allow"
        Action = [
          "acm:DescribeCertificate",
          "cloudwatch:DescribeAlarms",
          "ec2:Describe*",
          "ecr:DescribeRepositories", "ecr:GetRepositoryPolicy", "ecr:ListTagsForResource",
          "ecs:DescribeClusters", "ecs:DescribeServices", "ecs:DescribeTaskDefinition", "ecs:ListTagsForResource",
          "elasticloadbalancing:Describe*",
          "iam:GetRole", "iam:GetRolePolicy", "iam:ListAttachedRolePolicies", "iam:ListRolePolicies", "iam:ListRoleTags",
          "lambda:GetEventSourceMapping",
          "logs:DescribeLogGroups", "logs:DescribeMetricFilters", "logs:ListTagsForResource", "logs:ListTagsLogGroup",
          "mq:DescribeBroker", "mq:ListTags",
          "rds:DescribeDBInstances", "rds:DescribeDBSubnetGroups", "rds:ListTagsForResource",
          "route53:GetHostedZone", "route53:ListResourceRecordSets",
          "servicediscovery:GetNamespace", "servicediscovery:GetOperation", "servicediscovery:ListTagsForResource",
        ]
        Resource = "*"
      },
    ]
  })
}

output "github_actions_role_arns" {
  value = { for job, role in aws_iam_role.github : job => role.arn }
}
