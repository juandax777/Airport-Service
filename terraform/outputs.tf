output "ecr_repository_urls" {
  description = "URLs de los repositorios de imágenes para el pipeline."
  value = {
    airport      = aws_ecr_repository.airport.repository_url
    itinerary    = aws_ecr_repository.itinerary.repository_url
    notification = aws_ecr_repository.notification.repository_url
    web          = aws_ecr_repository.web.repository_url
  }
}
