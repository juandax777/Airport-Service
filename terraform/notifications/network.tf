locals {
  sources = merge(var.other_secrets_client_groups, {
    broker = var.broker_security_group
    worker = var.worker_security_group
  })

  endpoint_policies = {
    lambda = {
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
      Action    = "lambda:InvokeFunction"
      Resource  = "*"
    }
    sts = {
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
      Action    = "sts:AssumeRole"
      Resource  = "*"
    }
    secretsmanager = {
      Effect    = "Allow"
      Principal = "*"
      Action    = "secretsmanager:GetSecretValue"
      Resource  = "*"
    }
  }
}

resource "aws_security_group" "endpoint" {
  name   = "${var.name}-endpoints"
  vpc_id = var.vpc_id
}

resource "aws_vpc_security_group_ingress_rule" "endpoint" {
  for_each = local.sources

  security_group_id            = aws_security_group.endpoint.id
  referenced_security_group_id = each.value
  ip_protocol                  = "tcp"
  from_port                    = 443
  to_port                      = 443
}

resource "aws_vpc_security_group_egress_rule" "endpoint" {
  for_each = local.sources

  security_group_id            = each.value
  referenced_security_group_id = aws_security_group.endpoint.id
  ip_protocol                  = "tcp"
  from_port                    = 443
  to_port                      = 443
}

resource "aws_vpc_endpoint" "private" {
  for_each = local.endpoint_policies

  vpc_id              = var.vpc_id
  service_name        = "com.amazonaws.${var.region}.${each.key}"
  vpc_endpoint_type   = "Interface"
  private_dns_enabled = true
  subnet_ids          = var.subnet_ids
  security_group_ids  = [aws_security_group.endpoint.id]
  policy = jsonencode({
    Version   = "2012-10-17"
    Statement = [each.value]
  })
}
