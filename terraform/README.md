# Infraestructura AWS preparada

Terraform se mantiene como preparación; no ejecutar `apply` durante el desarrollo local.

El despliegue objetivo usa Amazon ECR para imágenes, ECS Fargate para Airport e Itinerary Service, RDS PostgreSQL con bases aisladas, Amazon MQ for RabbitMQ, Lambda para notificaciones, Secrets Manager y CloudWatch. GitHub Actions debe autenticarse mediante OIDC y ejecutar únicamente `terraform plan` hasta aprobar manualmente el entorno.
