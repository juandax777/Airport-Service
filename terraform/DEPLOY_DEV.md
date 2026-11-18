# Primer despliegue de dev en AWS

Usa Terraform desde tu equipo para crear la infraestructura y AWS CloudShell dentro de la VPC para inicializar PostgreSQL y RabbitMQ. Para reducir componentes y costo, parte de una región, una tarea por servicio, un NAT, una instancia RDS con dos bases y un broker de un nodo. El equipo accede desde las IPv4 que autorice. Si no tienes dominio, usa el DNS que asigna el balanceador y datos ficticios en la demo HTTP.

## 1. Preparar cuenta y versión

- Acuerda cuenta, región, dos zonas, presupuesto e IPv4 públicas del equipo. Para usar HTTPS, prepara además un dominio y un certificado ACM emitido en la región del ALB. Cotiza el broker de un nodo, RDS, Fargate, ALB, NAT y los endpoints de Lambda antes de crear el entorno. Activa alertas de presupuesto.
- Instala Terraform compatible con `versions.tf`, AWS CLI y Docker. El despliegue registrado se hizo con Terraform 1.17.2. Usa una sesión temporal de AWS y confirma la cuenta con `aws sts get-caller-identity`. Revisa los cambios y usa imágenes identificadas por digest.
- En `terraform/` y `terraform/bootstrap/`, genera y versiona `.terraform.lock.hcl` con `terraform providers lock -platform=windows_amd64 -platform=linux_amd64`. Si el equipo usa otras plataformas, inclúyelas. Los estados, planes guardados y valores reales van fuera de Git. [Bloqueo de proveedores](https://developer.hashicorp.com/terraform/cli/commands/providers/lock).

## 2. Crear estado, red y datos

Si el equipo ya tiene un backend aprobado, úsalo después de comprobar su cuenta y clave. Para uno nuevo, copia el ejemplo de `terraform/bootstrap` a `terraform.tfvars`, completa los datos y ejecuta desde la raíz del repositorio:

```powershell
terraform -chdir=terraform/bootstrap init
terraform -chdir=terraform/bootstrap plan
terraform -chdir=terraform/bootstrap apply
```

Confirma `apply` solo si la vista previa coincide con lo acordado. Crea los roles de GitHub del bootstrap únicamente si vas a publicar imágenes desde Actions. La [guía de bootstrap](bootstrap/README.md) explica cómo conservar un estado ECR previo en caso de que exista.

Copia `backend.dev.hcl.example` a `backend.dev.hcl` y `terraform.tfvars.example` a `terraform.tfvars` dentro de `terraform/`. Completa el backend y habilita `network`, `database` y `messaging`. Inyecta `TF_VAR_mq_admin_password` desde un almacén de secretos para cada sesión de Terraform que habilite el broker. Revisa que el tipo y la versión del broker estén disponibles en tu región. Deja `compute` y `notification_worker` sin configurar en esta etapa.

```powershell
terraform -chdir=terraform init '-backend-config=backend.dev.hcl'
terraform -chdir=terraform plan
terraform -chdir=terraform apply
terraform -chdir=terraform output -json network
terraform -chdir=terraform output -json data_services
terraform -chdir=terraform output -json ecr_repository_urls
```

## 3. Preparar imágenes, bases y cola

Publica las cuatro imágenes y guarda sus digests. Si configuraste OIDC, usa **Publish images to Amazon ECR** desde `main` con el entorno `dev`. Si prefieres publicar desde Docker local, inicia sesión en el registro ECR con AWS CLI y usa las URLs del último output. Construye Airport y Web con sus Dockerfiles y `--platform linux/amd64`. Para Itinerary agrega `--build-arg INCLUDE_RDS_CA=true`. Para Notification usa `docker buildx build --load --platform linux/amd64 --provenance=false -f services/notification_service/Dockerfile.lambda`, con la carpeta del servicio como contexto. Etiqueta cada imagen con el commit, publícala y consulta su digest en ECR. [Publicación con GitHub Actions](bootstrap/github-actions.md) · [Publicación manual en ECR](https://docs.aws.amazon.com/AmazonECR/latest/userguide/docker-push-ecr-image.html).

Abre una sesión CloudShell en una subred privada `app` con el grupo `operations`. Usa la [guía de operaciones](operations/README.md) para crear las dos bases, aplicar las migraciones y configurar el exchange, la cola y el enlace. Crea los secretos de aplicación para las dos bases y los secretos separados del publicador y del consumidor RabbitMQ. Conserva los ARN para configurar Terraform.

## 4. Levantar y comprobar la aplicación

Completa `compute` con los tres digests ECS, los ARN de los secretos y `allowed_web_cidrs` con las IP del equipo. Para la URL predeterminada de AWS, deja `hostname`, `certificate_arn` y `hosted_zone_id` sin configurar. Para HTTPS, configura el dominio y el certificado. Configura `notification_worker` con el digest de Lambda y sus dos ARN. Mantén `enabled = false` para la primera aplicación. Ejecuta `terraform -chdir=terraform plan`, revisa el resultado y aplica en la misma configuración. Consulta `terraform -chdir=terraform output -json compute` para obtener `web_url`. Si usas un dominio con DNS externo, apúntalo al ALB indicado allí.

Cuando los servicios estén saludables y hayas verificado la cola, cambia `notification_worker.enabled` a `true`, revisa y aplica el nuevo plan. Desde una IP autorizada, comprueba el mapa, la creación y edición de un itinerario y su fila en el historial de notificaciones. Comprueba que desde fuera de las redes autorizadas la web no sea accesible y que una entrega repetida del mismo `event_id` genere una sola fila. Usa datos ficticios.

Si una creación devuelve `503`, revisa primero si el itinerario quedó guardado. Evita repetir la creación hasta revisar el historial, los logs y el estado de la cola. La recuperación automática entre la escritura en PostgreSQL y la publicación en RabbitMQ queda pendiente de la decisión sobre Outbox.

Para una demostración temporal, acuerda cuándo retirar el entorno. ECS detenido no elimina los cargos de RDS, MQ, NAT, ALB ni endpoints. Revisa qué conservar antes de planificar el retiro. RDS tiene protección de borrado y requiere un snapshot final para su retirada. Conserva el backend separado mientras existan recursos que gestionar.

## Alternativa de demostración sin Terraform

1. Crea una EC2 Linux con volumen EBS cifrado y SSM Agent. Asigna un perfil de instancia que permita a Systems Manager gestionar la máquina y dale salida HTTPS hacia Systems Manager y los registros de imágenes. Mantén el grupo de seguridad sin reglas de entrada.
2. Entra por Session Manager, instala Docker y el plugin Compose, y obtén el código del repositorio. Copia `.env.example` a `.env`, configura credenciales propias y ejecuta `docker compose up -d --build`.
3. Desde tu equipo, con AWS CLI y el plugin de Session Manager, abre el túnel y visita `http://localhost:8000`. [Reenvío de puertos con Session Manager](https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager-working-with-sessions-start.html#sessions-start-port-forwarding).

   ```powershell
   aws ssm start-session --target i-REEMPLAZA --document-name AWS-StartPortForwardingSession --parameters 'portNumber=8000,localPortNumber=8000'
   ```

Esta opción permite demostrar el mapa, CRUD y notificaciones con el consumidor de Compose. Sirve para una presentación puntual. Si la entrega exige Lambda o los servicios administrados, usa el piloto Terraform. Los volúmenes de la EC2 son la persistencia de la demostración y deben respaldarse si el equipo necesita conservarlos.
