module "network" {
  source   = "./network"
  for_each = var.network == null ? {} : { primary = var.network }

  name               = local.name
  vpc_cidr           = each.value.vpc_cidr
  availability_zones = each.value.availability_zones
  nat_per_az         = each.value.nat_per_az
}

output "network" {
  description = "VPC y subredes por nivel y zona cuando se configura la red."
  value       = one(values(module.network))
}
