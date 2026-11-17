output "deployment" {
  value = {
    cluster_name   = aws_ecs_cluster.this.name
    web_url        = "https://${var.config.hostname}"
    alb_dns_name   = aws_lb.web.dns_name
    alb_zone_id    = aws_lb.web.zone_id
    service_names = {
      airport   = aws_ecs_service.airport.name
      itinerary = aws_ecs_service.itinerary.name
      web       = aws_ecs_service.web.name
    }
  }
}
