# Despliegue de Airport Service en AWS

Este documento registra el despliegue real del entorno `dev` en `us-east-1`. La [guía de despliegue](DEPLOY_DEV.md) contiene los pasos generales. La aplicación usa `https://viajaporcolombia.click` y acepta conexiones públicas IPv4. HTTP redirige a HTTPS.

## Estado del despliegue

| Etapa | Resultado |
|---|---|
| Estado remoto | Bootstrap aplicado. Se creó un bucket S3 con cifrado, versionado, bloqueo de acceso público y política de transporte seguro. `dev` usa la clave `dev/terraform.tfstate` y bloqueo nativo de Terraform. |
| Repositorios ECR | Terraform creó y AWS confirmó cuatro repositorios bajo `personal-itineraries-dev/`. |
| Versión e imágenes | Las imágenes iniciales usan la etiqueta `9592ccee0d9f`. Web se reconstruyó después con la corrección HTTPS y usa la etiqueta `fix-https-static-20261117`. Los cambios de esa corrección están locales, sin commit. |
| Validación local | Ruff pasó. Pytest pasó 40 pruebas y reportó 95,28 % de cobertura con la configuración actual del repositorio. Esto valida la suite local. La integración de AWS se comprueba aparte. |
| Red y datos | Aplicado: 52 altas, 0 cambios y 0 eliminaciones. RDS está `available`; RabbitMQ 4.3 `mq.m7g.medium` está `RUNNING`. Plan posterior sin cambios. |
| Datos de aplicación | CloudShell privado operativo. Se aplicaron las migraciones de ambas bases y se verificaron la cola, el enlace y los permisos de RabbitMQ. |
| Web y notificaciones | ECS y Lambda desplegados; dominio HTTPS público y consumidor de RabbitMQ habilitado. Verificaciones funcionales registradas abajo. |

## Dónde ver los recursos en AWS

Entra a la cuenta `juanda` (`200943221929`) y selecciona **US East (N. Virginia), `us-east-1`**. En Route 53 y S3 algunas vistas son globales. Los enlaces siguientes abren la sección de cada servicio. Busca los nombres indicados.

| Servicio | Qué se creó y dónde buscarlo |
|---|---|
| [Route 53 — dominios](https://us-east-1.console.aws.amazon.com/route53/domains/home?region=us-east-1#/) | Dominio registrado `viajaporcolombia.click`. |
| [Route 53 — zonas DNS](https://us-east-1.console.aws.amazon.com/route53/v2/hostedzones#ListRecordSets/Z0307945ZKWKOPT8CCVP) | Zona pública `viajaporcolombia.click` con alias A al ALB, NS, SOA y CNAME de validación del certificado. |
| [Certificate Manager — ACM](https://us-east-1.console.aws.amazon.com/acm/home?region=us-east-1#/certificates/list) | Certificado emitido para `viajaporcolombia.click`. Se solicitó por AWS CLI; el CNAME de validación también se creó fuera de Terraform. |
| [ECS — clústeres](https://us-east-1.console.aws.amazon.com/ecs/v2/clusters?region=us-east-1) | Clúster `personal-itineraries-dev`, con servicios `personal-itineraries-dev-airport`, `personal-itineraries-dev-itinerary` y `personal-itineraries-dev-web`. En cada servicio abre **Tasks** para ver sus contenedores Fargate. |
| [ECR — repositorios](https://us-east-1.console.aws.amazon.com/ecr/repositories?region=us-east-1) | Cuatro repositorios bajo `personal-itineraries-dev/`: `airport-service`, `itinerary-service`, `notification-service` y `web-app`. Allí se consultan imágenes, etiquetas, digests y escaneos. |
| [EC2 — balanceadores](https://us-east-1.console.aws.amazon.com/ec2/home?region=us-east-1#LoadBalancers:) | Application Load Balancer con nombre que empieza por `web-`. En **Listeners and rules** consulta HTTP 80 y HTTPS 443; en **Target groups**, el estado de la aplicación web. |
| [Lambda — funciones](https://us-east-1.console.aws.amazon.com/lambda/home?region=us-east-1#/functions) | `personal-itineraries-dev-notifications`. En **Configuration → Triggers** aparece Amazon MQ y la cola `notifications`. |
| [RDS — bases de datos](https://us-east-1.console.aws.amazon.com/rds/home?region=us-east-1#databases:) | Instancia privada `personal-itineraries-dev-itinerary`, PostgreSQL `db.t4g.micro`. Contiene las bases lógicas separadas `itineraries` y `notifications`; para consultar tablas se usa una conexión privada. |
| [Amazon MQ — brokers](https://us-east-1.console.aws.amazon.com/amazon-mq/home?region=us-east-1#/brokers) | `personal-itineraries-dev-rabbitmq`, RabbitMQ privado. Su consola de administración requiere acceso desde la VPC. Allí están el exchange `itineraries`, la cola `notifications` y su enlace. |
| [VPC — redes](https://us-east-1.console.aws.amazon.com/vpcconsole/home?region=us-east-1#vpcs:) | VPC `personal-itineraries-dev` con seis subredes, tablas de rutas, un internet gateway, un NAT gateway, grupos de seguridad y endpoints. Los tres endpoints de Lambda, STS y Secrets Manager están disponibles; AWS también muestra un endpoint administrado por servicio en esa VPC. |
| [Secrets Manager — secretos](https://us-east-1.console.aws.amazon.com/secretsmanager/listsecrets?region=us-east-1) | Seis secretos bajo `personal-itineraries-dev/` para bases, migradores y RabbitMQ. RDS administra además su secreto maestro. Los secretos de aplicación se crearon durante la inicialización y no pertenecen al estado Terraform principal. |
| [CloudWatch — grupos de logs](https://us-east-1.console.aws.amazon.com/cloudwatch/home?region=us-east-1#logsV2:log-groups) | `/ecs/personal-itineraries-dev/airport`, `/itinerary`, `/web` y `/aws/lambda/personal-itineraries-dev-notifications`. En **Alarms** aparecen alarmas de errores, limitación y cuarentena. |
| [IAM — roles](https://us-east-1.console.aws.amazon.com/iam/home?region=us-east-1#/roles) | Roles de ejecución ECS con prefijos `ecs-airport-`, `ecs-itinerary-`, `ecs-web-` y el rol `notifications-` de Lambda. |
| [S3 — buckets](https://s3.console.aws.amazon.com/s3/buckets?region=us-east-1) | `juanda-airport-service-dev-tfstate-638a3399a8c5`, que contiene el estado remoto principal en `dev/terraform.tfstate`. El bootstrap tiene un estado local separado. Evita abrir o compartir el contenido del estado porque contiene datos sensibles. |
| [Cloud Map — namespaces](https://us-east-1.console.aws.amazon.com/cloudmap/home?region=us-east-1#namespaces) | Namespace `personal-itineraries-dev`, usado por ECS Service Connect para la comunicación entre servicios. |
| [CloudShell](https://us-east-1.console.aws.amazon.com/cloudshell/home?region=us-east-1) | Entorno VPC `airport-dev-ops` para operaciones privadas. Su sesión puede detenerse por inactividad. |
| [Billing and Cost Management](https://console.aws.amazon.com/costmanagement/home) | **Bills** y **Cost Explorer** permiten revisar gastos y periodos de los servicios. Consulta también el costo del dominio y la zona DNS. |

El dominio, el certificado ACM, el CNAME de validación y los secretos de aplicación fueron creados fuera de la raíz principal de Terraform. La zona DNS se creó al registrar el dominio. El alias A, los servicios de aplicación, las reglas de red y el mapping de Lambda sí aparecen en el estado principal. El bucket del estado se administra desde `terraform/bootstrap` con su estado local separado.

## Acceso y estado de Terraform

AWS CLI inició sesión con credenciales temporales. Se usó el perfil `terraform-dev` con `credential_process` para que el proveedor AWS de Terraform pudiera obtenerlas desde el perfil autenticado. Durante estas primeras etapas ese perfil todavía correspondía a la identidad raíz. Las credenciales y los valores de entorno se mantienen fuera de este documento y de Git.

En Windows PowerShell 5.1 el argumento completo de `backend-config` va entre comillas. El bootstrap y los ECR ya existen. La fase de red y datos usa el archivo local ignorado `terraform/terraform.tfvars`; conserva las opciones `network`, `database` y `messaging` para que Terraform mantenga los recursos desplegados. Usa estos comandos para consultar el entorno desde la raíz del repositorio:

```powershell
$env:AWS_PROFILE = 'terraform-dev'
aws sts get-caller-identity
terraform -chdir=terraform init '-backend-config=backend.dev.hcl'
terraform -chdir=terraform validate
terraform -chdir=terraform state list
terraform -chdir=terraform output ecr_repository_urls
```

La contraseña inicial de MQ se generó aleatoriamente y se conserva cifrada con DPAPI en `terraform/.terraform/mq-admin-password.dpapi`, protegida por la cuenta Windows que la creó. El estado Terraform también conserva el valor sensible y el bucket remoto cifra los objetos. No imprimas ni compartas la contraseña, el estado ni planes guardados. Para ejecutar planes futuros desde la misma cuenta Windows, recupera la variable solo en memoria:

```powershell
$sealed = Get-Content -Raw 'terraform/.terraform/mq-admin-password.dpapi'
$secure = ConvertTo-SecureString $sealed
$ptr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
try {
    $env:TF_VAR_mq_admin_password = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr)
} finally {
    [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr)
}

terraform -chdir=terraform plan
Remove-Item Env:TF_VAR_mq_admin_password
```

`terraform.tfvars` tiene la red `10.40.0.0/20`, dos zonas, un NAT, RDS Single-AZ y MQ de un nodo. Si vuelves a clonar el repositorio o cambias de equipo, esta configuración no estará ahí porque se ignora por Git; restáurala siguiendo `terraform/terraform.tfvars.example` y gestiona la contraseña mediante un medio seguro. El archivo DPAPI solo se puede descifrar bajo la misma cuenta Windows en este equipo.

## Cómo se preparó la publicación

Cada imagen usa su carpeta de servicio como contexto. La imagen de Itinerary incluye la CA de RDS y la de Notification usa la imagen base y el Dockerfile de Lambda.

```powershell
$releaseTag = '9592ccee0d9f'
docker buildx build --load --platform linux/amd64 -t "personal-itineraries-dev/airport-service:$releaseTag" services/airport_service
docker buildx build --load --platform linux/amd64 --build-arg INCLUDE_RDS_CA=true -t "personal-itineraries-dev/itinerary-service:$releaseTag" services/itinerary_service
docker buildx build --load --platform linux/amd64 --provenance=false -f services/notification_service/Dockerfile.lambda -t "personal-itineraries-dev/notification-service:$releaseTag" services/notification_service
docker buildx build --load --platform linux/amd64 -t "personal-itineraries-dev/web-app:$releaseTag" services/web_app
```

La publicación etiquetó cada imagen con la URL de su repositorio privado y ejecutó `docker push`. El token de ECR se entregó a Docker por entrada estándar, con una configuración temporal para el registro. Después, `aws ecr describe-images` confirmó que la etiqueta publicada devolvía un digest en cada repositorio. [Publicación en ECR](https://docs.aws.amazon.com/AmazonECR/latest/userguide/docker-push-ecr-image.html)

| Repositorio bajo `personal-itineraries-dev/` | Digest confirmado por ECR |
|---|---|
| `airport-service` | `sha256:e914c8bdfafaba6bad3ed963292247e6d6c0ff627a3a0d2b859b150329638daf` |
| `itinerary-service` | `sha256:89fc0fd8dcaaa0d63da737ae9266a782ee5ffd3f98494ccbd69e67eb71a9534b` |
| `notification-service` | `sha256:065a40f36e8b77b8def1292e2432e2eb35b72b5ce4f7b507b846cb3258ef0643` |
| `web-app` inicial | `sha256:afb12fd7afc99ed35955e9ec44528246c33db593bae6a7c6b8d4c6aa9ac49d66` |
| `web-app` actual | `sha256:3aa41aac0137d44440378e8caaf5b8eafd5fe7b0f46080bc8076205ed2e45699` |

El escaneo básico inicial de las cuatro imágenes Linux AMD64 no reportó hallazgos críticos. Reportó 3 de severidad alta en Airport, 3 en Itinerary, 4 en Notification y 3 en la imagen Web inicial. Esos resultados son históricos y no describen necesariamente la imagen Web actual. Para las imágenes con un índice de manifiestos se consultó el digest del manifiesto Linux AMD64.

```powershell
$services = 'airport-service', 'itinerary-service', 'notification-service', 'web-app'
foreach ($service in $services) {
    aws ecr describe-images --region us-east-1 --repository-name "personal-itineraries-dev/$service" --image-ids 'imageTag=9592ccee0d9f' --query 'imageDetails[0].{Digest:imageDigest,Publicado:imagePushedAt}' --output table
}
```

## Estimación antes de levantar red y datos

Se consultó el catálogo oficial de `us-east-1` el 16 de noviembre de 2026. El broker RabbitMQ de un nodo `mq.m7g.medium` cuesta USD 0,1367/h y RDS PostgreSQL `db.t4g.micro` Single-AZ cuesta USD 0,016/h, más almacenamiento. Con un NAT y su IPv4 pública, la base ronda **USD 5 por 24 horas**. Al sumar tres tareas Fargate de 0,5 vCPU y 1 GiB, un ALB y tres endpoints en dos zonas, la demo completa ronda **USD 9 por 24 horas** antes de tráfico, uso del balanceador, cargos variables, créditos e impuestos. Las cifras estiman infraestructura activa. El gasto real depende del uso y de la duración. [Catálogo de AWS](https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/using-the-aws-price-list-bulk-api-fetching-price-list-files-manually.html) · [Precios del NAT y IPv4](https://aws.amazon.com/vpc/pricing/)

## Verificación de la demo

La demo está disponible en [viajaporcolombia.click](https://viajaporcolombia.click). En la comprobación de despliegue se obtuvieron 52 aeropuertos y se observó un aeropuerto en el mapa del navegador. Desde la API web se creó, consultó y editó un itinerario ficticio, se comprobó su persistencia, y se eliminó con respuesta 204. Su consulta posterior respondió 404. Un aeropuerto inexistente fue rechazado con 422.

La creación real produjo una fila `simulated_sent` en la base de notificaciones. Para comprobar idempotencia y cuarentena se invocó Lambda directamente con un lote en el formato de RabbitMQ que contenía dos copias del mismo evento y un mensaje inválido. Se verificó una sola fila para el evento y una fila en cuarentena. Esas dos comprobaciones usaron invocación directa; la entrega inicial sí recorrió RabbitMQ. El historial de las pruebas permanece en la base de notificaciones. El plan posterior de Terraform indicó que no había cambios.

## Próximas fases y estado detallado

El inventario se contrastó con AWS el **17 de noviembre de 2026**. Los resultados de las pruebas y precios conservan la fecha de su ejecución.

| Fase | Estado | Evidencia / condición para avanzar |
|---|---|---|
| Cuenta y acceso CLI | Hecho para las fases iniciales | `aws sts get-caller-identity` confirmó la cuenta `200943221929`. El perfil local `terraform-dev` usó una sesión temporal de la identidad raíz; preparar acceso limitado sigue recomendado. |
| Estado remoto y ECR | Hecho según las operaciones registradas | Bootstrap y cuatro repositorios confirmados. Web usa la imagen corregida posterior a `9592ccee0d9f`. |
| Calidad e imágenes | Hecho | Ruff, 40 pruebas con 95,28 % de cobertura, publicación y escaneo ECR documentados arriba. |
| Red, PostgreSQL y RabbitMQ | Hecho | `terraform apply`: 52 altas, 0 cambios y 0 eliminaciones. VPC en dos zonas, tres capas de subredes, un NAT, RDS PostgreSQL privado y Amazon MQ privado. RDS `available`, broker `RUNNING`; `terraform plan` posterior sin cambios. Esta fase activa cargos continuos. |
| Esquemas, usuarios y topología | Hecho | Las migraciones de `itineraries` y `notifications` se aplicaron desde CloudShell. Se verificaron permisos, conectividad TLS y topología RabbitMQ. |
| ECS y ALB HTTP | Aplicado | 36 altas, 0 cambios y 0 eliminaciones. Los tres servicios ECS reportaron una tarea activa de una deseada y `/health/live` respondió HTTP 200 a través del ALB. |
| Lambda y activación del consumidor | Hecho | Lambda está `Active`, el mapping está `Enabled` y una creación real produjo una notificación persistida. |
| Demostración por URL | Verificada | Mapa, 52 aeropuertos, CRUD por API web, validación, persistencia, notificación, idempotencia y cuarentena comprobados. |
| Retiro del entorno | Pendiente de decisión separada | No borrar recursos sin revisar datos y snapshot RDS; el backend remoto se conserva para mantener el estado. |

## Continuación guiada desde PowerShell

Los comandos de esta sección son una receta para la siguiente sesión. **No ejecutes `apply` hasta que se haya aprobado explícitamente el conjunto exacto de recursos y el gasto estimado.** Antes de empezar, confirma en la consola que `terraform-dev` ya no opera como raíz y que tiene permisos limitados a esta demo. Las primeras etapas utilizaron la identidad raíz; no es recomendable continuar administrando infraestructura con ella. No copies claves, contraseñas ni resultados de `terraform state` al chat o al repositorio.

### A. Comprobar identidad y estado actuales

Abre una PowerShell nueva en la raíz del repositorio. Inicia sesión con el perfil que el equipo haya preparado y confirma la cuenta antes de ejecutar Terraform:

```powershell
$env:AWS_PROFILE = 'terraform-dev'
$env:AWS_DEFAULT_REGION = 'us-east-1'
aws sts get-caller-identity
terraform -chdir=terraform init '-backend-config=backend.dev.hcl'
terraform -chdir=terraform validate
terraform -chdir=terraform state list
terraform -chdir=terraform output ecr_repository_urls
```

La cuenta debe ser `200943221929`. `terraform init` apunta al estado remoto existente; no inicialices otro backend ni cambies su clave. Para consultar una salida sensible, no uses `terraform output -json` en una terminal compartida ni pegues su resultado en una conversación. Consulta solo `network` y `data_services` cuando se necesiten para la sesión operativa.

### B. Revisar el plan de red y datos ya aplicados

El archivo ignorado `terraform/terraform.tfvars` contiene la configuración no secreta local y nunca se copia a Git. La configuración aplicada usa la red `10.40.0.0/20`, `us-east-1a` y `us-east-1b`, un NAT compartido, RDS PostgreSQL `db.t4g.micro` Single-AZ y un broker RabbitMQ de un nodo `mq.m7g.medium`. La contraseña inicial de MQ está protegida localmente con DPAPI y se inyecta en memoria como `TF_VAR_mq_admin_password`; no la escribas en argumentos, el historial del shell, el archivo de variables ni el documento.

```powershell
terraform -chdir=terraform plan
```

El plan de verificación posterior a la aplicación reportó **sin cambios**. En la creación, la primera llamada a `apply` no hizo cambios porque las variables opcionales estaban deshabilitadas. Se añadieron los valores no secretos a `terraform.tfvars`, se revisó el plan corregido de **52 altas, 0 cambios y 0 eliminaciones**, y con autorización se aplicó. Terraform confirmó **52 añadidos, 0 cambiados y 0 destruidos**. Si una revisión futura propone otros conteos, reemplazos o destrucciones, detente y revisa el estado antes de continuar.

La fase está aplicada. Estas salidas sirven para operaciones privadas. Trata los ARN de Secrets Manager como información interna y no compartas valores de secretos:

```powershell
terraform -chdir=terraform output -json network
terraform -chdir=terraform output -json data_services
```

`compute` y el event source mapping ya están habilitados; las bases lógicas, sus roles y migraciones están preparados.

### C. Inicializar datos por una conexión privada

El 17 de noviembre de 2026 se confirmó la sesión de `terraform-dev` en la cuenta `200943221929`. AWS reportó RDS `available`, RabbitMQ `RUNNING` y NAT `available`. Se creó CloudShell `airport-dev-ops` en la subred privada `app` de `us-east-1a`, con el grupo `operations`. Desde allí se comprobó la conexión TCP a PostgreSQL por el puerto 5432 y la respuesta HTTPS `401` esperada de RabbitMQ sin credenciales. Después se autenticó contra los dos servicios para aprovisionarlos.

El entorno CloudShell `airport-dev-ops` debe usar la VPC del proyecto, la subred privada `app` de `us-east-1a` y el grupo `operations`, todos obtenidos de las salidas anteriores. Al abrir la sesión, verificar primero la cuenta y luego el acceso a PostgreSQL y a la API de gestión de RabbitMQ. Los nombres de host se pueden obtener desde AWS CLI dentro de CloudShell sin recuperar contraseñas:

```bash
aws sts get-caller-identity --query Account --output text
export PGHOST="$(aws rds describe-db-instances --region us-east-1 --db-instance-identifier personal-itineraries-dev-itinerary --query 'DBInstances[0].Endpoint.Address' --output text)"
export MQ_CONSOLE_URL="$(aws mq describe-broker --region us-east-1 --broker-id b-df4c8793-9dbd-4181-bfe8-0b3751e6d870 --query 'BrokerInstances[0].ConsoleURL' --output text)"
timeout 5 bash -c '</dev/tcp/$PGHOST/5432' && echo 'PostgreSQL TCP OK'
curl --silent --show-error --max-time 10 --output /dev/null --write-out 'RabbitMQ HTTP %{http_code}\n' "${MQ_CONSOLE_URL%/}/api/overview"
```

Un `401` de RabbitMQ en la última consulta confirma que su API respondió por HTTPS y pide autenticación. La prueba TCP de PostgreSQL se completa después con una consulta autenticada usando `sslmode=verify-full`.

Usa la guía de [`operations/README.md`](operations/README.md) desde CloudShell dentro de la VPC. Esa tarea crea por separado las bases `itineraries` y `notifications`, sus roles de migración y aplicación, aplica las migraciones versionadas y declara el exchange, la cola y el binding. Registra credenciales independientes en AWS Secrets Manager. Las aplicaciones ECS/Lambda reciben ARN; cada secreto contiene la URI/JSON de su servicio. TLS de PostgreSQL debe usar `sslmode=verify-full`.

Orden de ejecución: bootstrap de PostgreSQL para `itineraries`, bootstrap para `notifications`, migración de cada base con su usuario migrador, creación de exchange topic `itineraries`, cola quorum `notifications`, binding `itinerary.created`, luego credenciales separadas del publicador y consumidor. No migres una base usando el rol de aplicación. Prueba las conexiones desde el ejecutor privado y no abras el SG de RDS o MQ a Internet.

#### Resultado aplicado

- CloudShell clonó el commit `d5f0654`. Antes de usarlo se confirmó con `git diff` que la carpeta de operaciones y las migraciones son idénticas a las de `9592cce`, el commit de las imágenes. Se preparó un entorno virtual temporal con `psycopg` y se descargó la CA oficial de RDS.
- Se ejecutó el bootstrap SQL con el usuario administrador de RDS y se aplicaron las migraciones con `migrate.py` usando cada rol migrador. Las credenciales separadas se generaron y guardaron en Secrets Manager. Las conexiones con los roles de aplicación y `sslmode=verify-full` confirmaron una tabla visible en `itineraries` y dos en `notifications`.
- Se ejecutó `bootstrap-rabbitmq.py` y se comprobó que `notifications` es una cola quorum durable enlazada al exchange `itineraries` mediante `itinerary.created`. El publicador tiene permiso de escritura sobre el exchange y el consumidor de Lambda tiene permiso de lectura de la cola. La credencial inicial del broker se leyó en memoria desde el estado remoto para esta operación.
- Se crearon seis secretos bajo `personal-itineraries-dev/`: `itineraries/database-url`, `itineraries/migrator`, `notifications/database-url`, `notifications/migrator`, `rabbitmq/publisher-url` y `rabbitmq/consumer`. Terraform usa los ARN de los cuatro secretos de aplicación. Los secretos de migración quedan para operaciones.

### D. Desplegar servicios web

Por solicitud expresa del propietario se abrieron los puertos 80 y 443 del ALB a `0.0.0.0/0`. Terraform creó dos reglas públicas y retiró las dos reglas anteriores limitadas a una IP. AWS confirmó las reglas, HTTPS respondió 200 en `/health/live` y HTTP devolvió 301 a HTTPS. La aplicación no solicita autenticación y los itinerarios son compartidos, por lo que cualquier visitante puede consultarlos y modificarlos. El ALB está configurado para IPv4; no se ha configurado acceso IPv6.

Se corrigieron las plantillas web para generar rutas relativas de CSS y JavaScript. El HTML HTTPS anterior incluía enlaces HTTP que el navegador bloqueaba. La imagen corregida se publicó con digest `sha256:3aa41aac0137d44440378e8caaf5b8eafd5fe7b0f46080bc8076205ed2e45699` y Terraform actualizó la tarea web. ECS completó el despliegue. La página de creación muestra ahora rutas `/static/` y el CSS responde HTTP 200 con `text/css`.

Se registró `viajaporcolombia.click` en Route 53. El registro figura `SUCCESSFUL` y el dominio `ACTIVE`. ACM emitió el certificado en `us-east-1` tras validar el CNAME en la zona pública. Terraform aplicó 3 altas, 1 cambio y 0 eliminaciones para el registro alias, HTTPS y redirección desde HTTP. HTTPS devolvió 200 en `/health/live` y HTTP devolvió 301 hacia HTTPS. Posteriormente se autorizó el acceso público IPv4. El proveedor Terraform mostró una advertencia sobre `target_group_arn` en la redirección que debe corregirse antes de actualizar el proveedor.

El plan inicial se aplicó con 36 altas. AWS confirmó una tarea activa para cada servicio. La entrada actual es `https://viajaporcolombia.click`; las comprobaciones funcionales están registradas en la sección de verificación.

El plan inicial de ECS y ALB arrojó **36 altas, 0 cambios y 0 eliminaciones**. Incluyó tres servicios Fargate, sus roles y logs, Service Connect y el ALB. El dominio, el acceso público y Lambda se agregaron posteriormente.

El bloque local `compute` incluye los digests activos, los ARN de los secretos, el dominio, el certificado y la zona DNS. `allowed_web_cidrs` es `0.0.0.0/0` por decisión del propietario y requiere HTTPS. Para limitar el acceso, cambia esa lista a las IPv4 autorizadas en formato `/32` y revisa el plan antes de aplicarlo.

```powershell
terraform -chdir=terraform plan
```

Revisa las altas del ALB, ECS, roles, logs y grupos de seguridad; comprueba que las imágenes están referidas por sus digests y que los secretos solo pasan por ARN. Confirma que no hay modificaciones de red, RDS, MQ, ECR ni backend no esperadas. Presenta y autoriza este `apply` como una fase separada. Al terminar:

```powershell
terraform -chdir=terraform output -json compute
```

Usa `web_url` para la prueba en navegador. Espera que ECS indique las tareas como `RUNNING` y que el target del ALB esté saludable. La ruta `/health/live` comprueba la disponibilidad HTTP de Web App, no todas las dependencias; la creación de itinerarios es la comprobación funcional de DB y broker.

### E. Preparar y activar notificaciones Lambda

Se aplicó el plan autorizado con 22 altas. La función `personal-itineraries-dev-notifications` está `Active` y su última actualización fue `Successful`. El mapping `76f607d8-1869-49d7-98bf-b309a4c6160f` se habilitó con Terraform mediante un cambio en sitio. Los tres endpoints privados y las alarmas están creados. Una notificación producida por un itinerario de prueba quedó persistida en PostgreSQL con estado `simulated_sent`.

El bloque `notification_worker` ya está configurado con `enabled = true`. Consulta el estado del mapping y los errores en Lambda y CloudWatch antes de cualquier operación adicional sobre la cola.

### F. Completar la prueba funcional y el registro

Los resultados de las pruebas ejecutadas aparecen en «Verificación de la demo». La aplicación acepta IPv4 pública y no exige autenticación. Usa datos ficticios y consulta ECS, los targets y los errores de Lambda para diagnósticos posteriores.

Si una creación responde `503`, comprueba primero si guardó el itinerario y si el mensaje llegó al broker antes de volver a enviar la solicitud. No hay transactional outbox en esta implementación: un fallo entre la transacción PostgreSQL y la publicación RabbitMQ puede dejar una creación guardada sin evento.

## Costos y apagado

La estimación anterior, **~USD 5/día para red y datos y ~USD 9/día con los servicios web y endpoints de Lambda**, es una aproximación para los tamaños indicados en `us-east-1`, no una cotización ni un límite de gasto. Tráfico, horas exactas, ALB, almacenamiento, snapshots, logs, precios vigentes, créditos e impuestos cambian el total. Revisa AWS Billing y configura alertas de presupuesto. Detener tareas ECS o deshabilitar Lambda no detiene el costo de RDS, RabbitMQ, NAT, ALB, IPv4 pública y endpoints que sigan aprovisionados.

El retiro debe hacerse con una revisión y autorización separadas. Primero registra si se conservarán datos; revisa la protección contra borrado y el snapshot final de RDS. Después revisa el plan de destrucción y elimina solo los componentes de demo aprobados. **Conserva el bucket/estado remoto hasta que no queden recursos administrados por ese estado**; destruir el backend antes puede impedir gestionar o recuperar la infraestructura restante. Tras el retiro, vuelve a consultar Billing para comprobar que no queden cargos de los recursos del proyecto.
