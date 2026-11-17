locals {
  port = 8000
  aliases = {
    airport   = "airport-service"
    itinerary = "itinerary-service"
  }

  environment = {
    airport = {}
    itinerary = {
      AIRPORT_SERVICE_URL      = "http://${local.aliases.airport}:${local.port}"
      DATABASE_AUTO_CREATE     = "false"
      RABBITMQ_DECLARE_TOPOLOGY = "false"
      PGSSLROOTCERT             = "/app/rds-global-bundle.pem"
    }
    web = {
      AIRPORT_SERVICE_URL   = "http://${local.aliases.airport}:${local.port}"
      ITINERARY_SERVICE_URL = "http://${local.aliases.itinerary}:${local.port}"
    }
  }

  itinerary_secrets = {
    DATABASE_URL = var.config.itinerary_db_secret
    RABBITMQ_URL = var.config.rabbitmq_url_secret
  }
}

resource "aws_ecs_cluster" "this" {
  name = var.name
}

resource "aws_service_discovery_http_namespace" "this" {
  name = var.name
}

resource "aws_cloudwatch_log_group" "service" {
  for_each = var.repositories

  name              = "/ecs/${var.name}/${each.key}"
  retention_in_days = var.config.log_retention_days
}

resource "aws_ecs_task_definition" "service" {
  for_each = var.repositories

  family                   = "${var.name}-${each.key}"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = 512
  memory                   = 1024
  execution_role_arn       = aws_iam_role.execution[each.key].arn

  runtime_platform {
    operating_system_family = "LINUX"
    cpu_architecture        = "X86_64"
  }

  container_definitions = jsonencode([{
    name      = each.key
    image     = "${each.value.url}@${var.config.image_digests[each.key]}"
    essential = true
    portMappings = [{
      name          = "http"
      containerPort = local.port
      protocol      = "tcp"
      appProtocol   = "http"
    }]
    environment = [
      for name, value in local.environment[each.key] : { name = name, value = value }
    ]
    secrets = [
      for name, arn in (each.key == "itinerary" ? local.itinerary_secrets : {}) :
      { name = name, valueFrom = arn }
    ]
    healthCheck = {
      command = [
        "CMD",
        "python",
        "-c",
        "import urllib.request; urllib.request.urlopen('http://127.0.0.1:${local.port}/health/live', timeout=3).close()"
      ]
      interval    = 30
      timeout     = 5
      retries     = 3
      startPeriod = 20
    }
    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = aws_cloudwatch_log_group.service[each.key].name
        "awslogs-region"        = var.region
        "awslogs-stream-prefix" = "app"
      }
    }
  }])
}
