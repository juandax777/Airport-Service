# Infraestructura AWS preparada

Terraform se mantiene como preparación; no ejecutar `apply` durante el desarrollo local.

El despliegue objetivo usa Amazon ECR para imágenes, ECS Fargate para Airport e Itinerary Service, RDS PostgreSQL con bases aisladas, Amazon MQ for RabbitMQ, Lambda para notificaciones, Secrets Manager y CloudWatch. GitHub Actions debe autenticarse mediante OIDC y ejecutar únicamente `terraform plan` hasta aprobar manualmente el entorno.

## Estructura propuesta

Los directorios siguientes contienen únicamente comentarios para orientar la implementación futura; todavía no están conectados como módulos y no crean recursos:

- `network/`: red, acceso y conectividad.
- `containers/`: imágenes, servicios ECS y entrada web.
- `database/`: PostgreSQL y aislamiento de datos.
- `messaging/`: RabbitMQ y topología de eventos.
- `notifications/`: función Lambda y consumo de eventos.
- `security/`: permisos y gestión de secretos.
- `monitoring/`: registros, métricas y alertas.

Cada directorio reserva `main.tf`, `variables.tf` y `outputs.tf` para su futura implementación. Los recursos ECR ya declarados en el directorio raíz se mantienen allí; antes de trasladarlos será necesario planear la migración del estado para evitar reemplazos. La configuración del estado remoto, el bloqueo y la separación de entornos también quedan pendientes. No guardar credenciales, estados ni planes en el repositorio.
