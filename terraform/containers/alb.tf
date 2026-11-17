resource "aws_lb" "web" {
  name_prefix               = "web-"
  load_balancer_type        = "application"
  internal                  = false
  subnets                   = var.public_subnet_ids
  security_groups           = [aws_security_group.component["alb"].id]
  drop_invalid_header_fields = true

  tags = { Name = "${var.name}-web" }
}

resource "aws_lb_target_group" "web" {
  name_prefix = "web-"
  target_type = "ip"
  port        = local.port
  protocol    = "HTTP"
  vpc_id      = var.vpc_id

  health_check {
    path    = "/health/live"
    matcher = "200"
  }

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_lb_listener" "redirect" {
  load_balancer_arn = aws_lb.web.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type = "redirect"

    redirect {
      host        = var.config.hostname
      port        = "443"
      protocol    = "HTTPS"
      status_code = "HTTP_301"
    }
  }
}

resource "aws_lb_listener" "https" {
  load_balancer_arn = aws_lb.web.arn
  port              = 443
  protocol          = "HTTPS"
  certificate_arn   = var.config.certificate_arn
  ssl_policy        = "ELBSecurityPolicy-TLS13-1-2-2021-06"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.web.arn
  }
}

resource "aws_route53_record" "web" {
  count = var.config.hosted_zone_id == null ? 0 : 1

  zone_id = var.config.hosted_zone_id
  name    = var.config.hostname
  type    = "A"

  alias {
    name                   = aws_lb.web.dns_name
    zone_id                = aws_lb.web.zone_id
    evaluate_target_health = true
  }
}
