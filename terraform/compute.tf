module "containers" {
  source = "./containers"
  count  = var.compute == null ? 0 : 1

  name                    = local.name
  region                  = var.aws_region
  vpc_id                  = module.network["primary"].vpc_id
  public_subnet_ids       = values(module.network["primary"].subnet_ids.public)
  private_subnet_ids      = values(module.network["primary"].subnet_ids.app)
  itinerary_data_group_id = aws_security_group.data_client["itinerary"].id

  repositories = {
    airport   = { url = aws_ecr_repository.airport.repository_url, arn = aws_ecr_repository.airport.arn }
    itinerary = { url = aws_ecr_repository.itinerary.repository_url, arn = aws_ecr_repository.itinerary.arn }
    web       = { url = aws_ecr_repository.web.repository_url, arn = aws_ecr_repository.web.arn }
  }

  config = var.compute

  depends_on = [
    module.network,
    module.database,
    module.messaging,
    aws_vpc_security_group_ingress_rule.postgres,
    aws_vpc_security_group_egress_rule.postgres,
    aws_vpc_security_group_ingress_rule.amqps,
    aws_vpc_security_group_egress_rule.amqps,
  ]
}

output "compute" {
  description = "Referencias del clúster y del punto de entrada HTTPS."
  value       = one(module.containers[*].deployment)
}
