resource "aws_ecs_service" "airport" {
  name                  = "${var.name}-airport"
  cluster               = aws_ecs_cluster.this.id
  launch_type           = "FARGATE"
  task_definition       = aws_ecs_task_definition.service["airport"].arn
  desired_count         = var.config.desired_count
  platform_version      = "1.4.0"
  wait_for_steady_state = true

  deployment_circuit_breaker {
    enable   = true
    rollback = true
  }

  network_configuration {
    subnets          = var.private_subnet_ids
    security_groups  = [aws_security_group.component["airport"].id]
    assign_public_ip = false
  }

  service_connect_configuration {
    enabled   = true
    namespace = aws_service_discovery_http_namespace.this.arn

    service {
      port_name      = "http"
      discovery_name = local.aliases.airport

      client_alias {
        dns_name = local.aliases.airport
        port     = local.port
      }
    }
  }

  depends_on = [
    aws_iam_role_policy.execution,
    aws_vpc_security_group_egress_rule.https,
    aws_vpc_security_group_ingress_rule.app,
    aws_vpc_security_group_egress_rule.app,
  ]
}

resource "aws_ecs_service" "itinerary" {
  name                  = "${var.name}-itinerary"
  cluster               = aws_ecs_cluster.this.id
  launch_type           = "FARGATE"
  task_definition       = aws_ecs_task_definition.service["itinerary"].arn
  desired_count         = var.config.desired_count
  platform_version      = "1.4.0"
  wait_for_steady_state = true

  deployment_circuit_breaker {
    enable   = true
    rollback = true
  }

  network_configuration {
    subnets          = var.private_subnet_ids
    security_groups  = [aws_security_group.component["itinerary"].id, var.itinerary_data_group_id]
    assign_public_ip = false
  }

  service_connect_configuration {
    enabled   = true
    namespace = aws_service_discovery_http_namespace.this.arn

    service {
      port_name      = "http"
      discovery_name = local.aliases.itinerary

      client_alias {
        dns_name = local.aliases.itinerary
        port     = local.port
      }
    }
  }

  depends_on = [
    aws_iam_role_policy.execution,
    aws_vpc_security_group_egress_rule.https,
    aws_vpc_security_group_ingress_rule.app,
    aws_vpc_security_group_egress_rule.app,
    aws_ecs_service.airport,
  ]
}

resource "aws_ecs_service" "web" {
  name                  = "${var.name}-web"
  cluster               = aws_ecs_cluster.this.id
  launch_type           = "FARGATE"
  task_definition       = aws_ecs_task_definition.service["web"].arn
  desired_count         = var.config.desired_count
  platform_version      = "1.4.0"
  wait_for_steady_state = true
  health_check_grace_period_seconds = 60

  deployment_circuit_breaker {
    enable   = true
    rollback = true
  }

  network_configuration {
    subnets          = var.private_subnet_ids
    security_groups  = [aws_security_group.component["web"].id]
    assign_public_ip = false
  }

  service_connect_configuration {
    enabled   = true
    namespace = aws_service_discovery_http_namespace.this.arn
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.web.arn
    container_name   = "web"
    container_port   = local.port
  }

  depends_on = [
    aws_iam_role_policy.execution,
    aws_vpc_security_group_egress_rule.https,
    aws_vpc_security_group_ingress_rule.app,
    aws_vpc_security_group_egress_rule.app,
    aws_ecs_service.itinerary,
    aws_lb_listener.https,
  ]
}
