locals {
  data_enabled = var.database != null || var.messaging != null
  db_instances = var.database == null ? toset([]) : (
    var.database.separate_instances ? toset(["itinerary", "notification"]) : toset(["itinerary"])
  )

  database_clients = {
    for instance in local.db_instances : instance => (
      instance == "notification" ? ["notification", "operations"] :
      var.database.separate_instances ? ["itinerary", "operations"] :
      ["itinerary", "notification", "operations"]
    )
  }

  database_rules = {
    for rule in flatten([
      for instance, clients in local.database_clients : [
        for client in clients : { instance = instance, client = client }
      ]
    ]) : "${rule.instance}/${rule.client}" => rule
  }

  broker_clients = var.messaging == null ? toset([]) : toset(["itinerary", "notification", "operations", "broker"])
}

resource "aws_security_group" "data_client" {
  for_each = local.data_enabled ? toset(["itinerary", "notification", "operations"]) : toset([])

  name   = "${local.name}-${each.key}-data-client"
  vpc_id = module.network["primary"].vpc_id
}

resource "aws_security_group" "database" {
  for_each = local.db_instances

  name   = "${local.name}-${each.key}-postgres"
  vpc_id = module.network["primary"].vpc_id
}

resource "aws_vpc_security_group_ingress_rule" "postgres" {
  for_each = local.database_rules

  security_group_id            = aws_security_group.database[each.value.instance].id
  referenced_security_group_id = aws_security_group.data_client[each.value.client].id
  ip_protocol                  = "tcp"
  from_port                    = 5432
  to_port                      = 5432
}

resource "aws_vpc_security_group_egress_rule" "postgres" {
  for_each = local.database_rules

  security_group_id            = aws_security_group.data_client[each.value.client].id
  referenced_security_group_id = aws_security_group.database[each.value.instance].id
  ip_protocol                  = "tcp"
  from_port                    = 5432
  to_port                      = 5432
}

resource "aws_security_group" "broker" {
  count = var.messaging != null ? 1 : 0

  name   = "${local.name}-rabbitmq"
  vpc_id = module.network["primary"].vpc_id
}

locals {
  broker_client_groups = {
    for client in local.broker_clients : client => (
      client == "broker" ? aws_security_group.broker[0].id : aws_security_group.data_client[client].id
    )
  }
}

resource "aws_vpc_security_group_ingress_rule" "amqps" {
  for_each = local.broker_clients

  security_group_id            = aws_security_group.broker[0].id
  referenced_security_group_id = local.broker_client_groups[each.key]
  ip_protocol                  = "tcp"
  from_port                    = 5671
  to_port                      = 5671
}

resource "aws_vpc_security_group_egress_rule" "amqps" {
  for_each = local.broker_clients

  security_group_id            = local.broker_client_groups[each.key]
  referenced_security_group_id = aws_security_group.broker[0].id
  ip_protocol                  = "tcp"
  from_port                    = 5671
  to_port                      = 5671
}

resource "aws_vpc_security_group_ingress_rule" "broker_management" {
  count = var.messaging != null ? 1 : 0

  security_group_id            = aws_security_group.broker[0].id
  referenced_security_group_id = aws_security_group.data_client["operations"].id
  ip_protocol                  = "tcp"
  from_port                    = 443
  to_port                      = 443
}

resource "aws_vpc_security_group_egress_rule" "broker_management" {
  count = var.messaging != null ? 1 : 0

  security_group_id            = aws_security_group.data_client["operations"].id
  referenced_security_group_id = aws_security_group.broker[0].id
  ip_protocol                  = "tcp"
  from_port                    = 443
  to_port                      = 443
}

module "database" {
  source = "./database"
  count  = var.database != null ? 1 : 0

  name               = local.name
  subnet_ids         = values(module.network["primary"].subnet_ids.data)
  instances          = local.db_instances
  security_group_ids = { for name, sg in aws_security_group.database : name => sg.id }
  engine_version     = var.database.engine_version
  instance_class     = var.database.instance_class
  storage_gib        = var.database.storage_gib
  multi_az           = var.database.multi_az
}

module "messaging" {
  source = "./messaging"
  count  = var.messaging != null ? 1 : 0

  name    = "${local.name}-rabbitmq"
  cluster = var.messaging.cluster
  subnet_ids = var.messaging.cluster ? values(module.network["primary"].subnet_ids.data) : [
    module.network["primary"].subnet_ids.data[var.network.availability_zones[0]]
  ]
  security_group_id = aws_security_group.broker[0].id
  engine_version    = var.messaging.engine_version
  instance_type     = var.messaging.instance_type
  admin_username    = var.messaging.admin_username
  admin_password    = var.mq_admin_password
}

output "data_services" {
  description = "Referencias para desplegar y configurar las cargas privadas."
  value = {
    databases = try(module.database[0].instances, {})
    broker    = try(module.messaging[0].broker, null)
    client_security_groups = {
      for name, sg in aws_security_group.data_client : name => sg.id
    }
  }
}
