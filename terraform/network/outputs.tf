output "vpc_id" {
  value = aws_vpc.this.id
}

output "subnet_ids" {
  description = "Identificadores de subred por nivel y zona."
  value = {
    for tier in keys(local.tiers) : tier => {
      for az in var.availability_zones : az => aws_subnet.this["${tier}/${az}"].id
    }
  }
}
