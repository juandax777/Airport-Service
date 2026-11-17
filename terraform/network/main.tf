locals {
  tiers = {
    public = 0
    app    = 4
    data   = 8
  }

  subnets = merge([
    for tier, offset in local.tiers : {
      for index, az in var.availability_zones : "${tier}/${az}" => {
        tier = tier
        az   = az
        cidr = cidrsubnet(var.vpc_cidr, 4, offset + index)
      }
    }
  ]...)

  nat_zones = toset(var.nat_per_az ? var.availability_zones : slice(var.availability_zones, 0, 1))
}

resource "aws_vpc" "this" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = { Name = var.name }
}

resource "aws_subnet" "this" {
  for_each = local.subnets

  vpc_id                  = aws_vpc.this.id
  availability_zone       = each.value.az
  cidr_block              = each.value.cidr
  map_public_ip_on_launch = false

  tags = { Name = "${var.name}-${each.value.tier}-${each.value.az}" }
}

resource "aws_internet_gateway" "this" {
  vpc_id = aws_vpc.this.id
  tags   = { Name = var.name }
}

resource "aws_eip" "nat" {
  for_each = local.nat_zones

  domain = "vpc"
  tags   = { Name = "${var.name}-nat-${each.key}" }
}

resource "aws_nat_gateway" "this" {
  for_each = local.nat_zones

  subnet_id     = aws_subnet.this["public/${each.key}"].id
  allocation_id = aws_eip.nat[each.key].id
  tags          = { Name = "${var.name}-${each.key}" }

  depends_on = [aws_internet_gateway.this]
}

resource "aws_route_table" "this" {
  for_each = local.subnets

  vpc_id = aws_vpc.this.id
  tags   = { Name = "${var.name}-${each.value.tier}-${each.value.az}" }
}

resource "aws_route" "internet" {
  for_each = toset(var.availability_zones)

  route_table_id         = aws_route_table.this["public/${each.key}"].id
  destination_cidr_block = "0.0.0.0/0"
  gateway_id             = aws_internet_gateway.this.id
}

resource "aws_route" "nat" {
  for_each = toset(var.availability_zones)

  route_table_id         = aws_route_table.this["app/${each.key}"].id
  destination_cidr_block = "0.0.0.0/0"
  nat_gateway_id         = aws_nat_gateway.this[var.nat_per_az ? each.key : var.availability_zones[0]].id
}

resource "aws_route_table_association" "this" {
  for_each = local.subnets

  subnet_id      = aws_subnet.this[each.key].id
  route_table_id = aws_route_table.this[each.key].id
}

resource "aws_default_security_group" "this" {
  vpc_id = aws_vpc.this.id
  tags   = { Name = "${var.name}-default-restricted" }
}
