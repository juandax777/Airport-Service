locals {
  app_flows = {
    "alb/web" = { from = "alb", to = "web" }
    "web/airport" = { from = "web", to = "airport" }
    "web/itinerary" = { from = "web", to = "itinerary" }
    "itinerary/airport" = { from = "itinerary", to = "airport" }
  }
}

resource "aws_security_group" "component" {
  for_each = toset(["alb", "airport", "itinerary", "web"])

  name   = "${var.name}-${each.key}-compute"
  vpc_id = var.vpc_id
}

resource "aws_vpc_security_group_ingress_rule" "team_web" {
  for_each = {
    for pair in setproduct(var.config.allowed_web_cidrs, [80, 443]) :
    "${pair[0]}:${pair[1]}" => { cidr = pair[0], port = pair[1] }
  }

  security_group_id = aws_security_group.component["alb"].id
  cidr_ipv4         = each.value.cidr
  ip_protocol      = "tcp"
  from_port        = each.value.port
  to_port          = each.value.port
}

resource "aws_vpc_security_group_ingress_rule" "app" {
  for_each = local.app_flows

  security_group_id            = aws_security_group.component[each.value.to].id
  referenced_security_group_id = aws_security_group.component[each.value.from].id
  ip_protocol                  = "tcp"
  from_port                    = local.port
  to_port                      = local.port
}

resource "aws_vpc_security_group_egress_rule" "app" {
  for_each = local.app_flows

  security_group_id            = aws_security_group.component[each.value.from].id
  referenced_security_group_id = aws_security_group.component[each.value.to].id
  ip_protocol                  = "tcp"
  from_port                    = local.port
  to_port                      = local.port
}

resource "aws_vpc_security_group_egress_rule" "https" {
  for_each = var.repositories

  security_group_id = aws_security_group.component[each.key].id
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol      = "tcp"
  from_port        = 443
  to_port          = 443
}
