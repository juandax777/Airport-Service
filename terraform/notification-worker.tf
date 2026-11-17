module "notifications" {
  source = "./notifications"
  count  = var.notification_worker == null ? 0 : 1

  name                  = "${local.name}-notifications"
  region                = var.aws_region
  vpc_id                = module.network["primary"].vpc_id
  subnet_ids            = values(module.network["primary"].subnet_ids.data)
  worker_security_group = aws_security_group.data_client["notification"].id
  broker_security_group = aws_security_group.broker[0].id
  broker_arn            = module.messaging[0].broker.arn
  repository_url        = aws_ecr_repository.notification.repository_url
  repository_name       = aws_ecr_repository.notification.name
  other_secrets_client_groups = {
    itinerary  = aws_security_group.data_client["itinerary"].id
    operations = aws_security_group.data_client["operations"].id
  }

  config = var.notification_worker

  depends_on = [
    module.database,
    aws_vpc_security_group_ingress_rule.postgres,
    aws_vpc_security_group_egress_rule.postgres,
    aws_vpc_security_group_ingress_rule.amqps,
    aws_vpc_security_group_egress_rule.amqps,
  ]
}

module "notification_monitoring" {
  source = "./monitoring"
  count  = var.notification_worker == null ? 0 : 1

  function_name = module.notifications[0].worker.function_name
  log_group     = module.notifications[0].worker.log_group
  alarm_actions = var.notification_worker.alarm_actions
}

output "notification_worker" {
  value = var.notification_worker == null ? null : merge(module.notifications[0].worker, {
    alarm_names = module.notification_monitoring[0].alarm_names
  })
}
