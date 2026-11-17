resource "aws_mq_broker" "this" {
  broker_name                = var.name
  engine_type                = "RabbitMQ"
  engine_version             = var.engine_version
  host_instance_type         = var.instance_type
  deployment_mode            = var.cluster ? "CLUSTER_MULTI_AZ" : "SINGLE_INSTANCE"
  subnet_ids                 = var.subnet_ids
  security_groups            = [var.security_group_id]
  publicly_accessible        = false
  auto_minor_version_upgrade = true

  encryption_options {
    use_aws_owned_key = true
  }

  logs {
    general = true
  }

  user {
    username = var.admin_username
    password = var.admin_password
  }

  lifecycle {
    precondition {
      condition     = length(var.subnet_ids) == (var.cluster ? 3 : 1)
      error_message = "RabbitMQ requiere una subred para instancia única o tres para clúster."
    }
  }
}
