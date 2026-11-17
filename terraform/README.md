# Infraestructura AWS

La raíz declara cuatro repositorios ECR con escaneo al publicar. Se conservan los nombres y las direcciones Terraform de Airport, Itinerary y Notification. Web App tiene su propio repositorio. Las declaraciones no acreditan que los repositorios existan en AWS. La fase 2 declara el backend S3, su bootstrap y un módulo de red optativo. La fase 3 agrega RDS y Amazon MQ privados y un flujo de aprovisionamiento y migración desde un ejecutor privado. La fase 4 declara ECS Fargate, comunicación privada y entrada HTTPS. La fase 5 declara Lambda con consumo de Amazon MQ y alarmas de notificaciones.

Docker Compose sigue siendo el entorno local. Allí Web App consume Airport e Itinerary, Itinerary valida aeropuertos y publica a RabbitMQ, y el consumidor en contenedor registra las notificaciones en su propia base. Cada servicio persistente tiene una migración SQL inicial versionada. El arranque de la aplicación y el flujo de migraciones deberán revisarse juntos antes del despliegue.

| Fase | Trabajo y dependencias | Criterio de aceptación |
|---|---|---|
| 1. Registro de imágenes | Corregir HCL y agregar ECR para Web App. Revisar el estado real antes de cualquier operación. | El plan futuro conserva las direcciones existentes y agrega Web App. Si hay repositorios creados fuera de Terraform, reconciliar mediante importación antes de crear. |
| 2. Estado y red | Crear el backend en una raíz de bootstrap separada. Confirmar cuenta, región, CIDR y dos AZ. Diseñar subredes públicas para ALB/NAT, privadas para ECS y privadas para datos. Configurar DNS y grupos de seguridad por componente. | El estado queda cifrado, versionado y con bloqueo. Solo el ALB recibe tráfico público. Las tareas pueden descargar imágenes y enviar logs. Airport puede alcanzar API Colombia por HTTPS. |
| 3. Datos y RabbitMQ | Aprovisionar RDS y Amazon MQ privados. Crear bases, roles y secretos por servicio y configurar el exchange, cola y binding. Ejecutar migraciones con tareas puntuales privadas antes de activar sus consumidores. | Usuarios de aplicación sin permisos cruzados. Migraciones registradas por versión y ejecutadas por un rol de migración. Publicación por AMQPS y topología durable disponible antes de habilitar escrituras. |
| 4. Web y servicios | Construir las tres imágenes ECS desde sus Dockerfiles y desplegar por digest tras publicación autorizada. Configurar Service Connect para nombres privados, URLs internas y el ALB con ACM y DNS. Crear logs desde esta fase. | HTTPS sirve Web App y redirige HTTP. El ALB registra únicamente Web App y usa su ruta /health/live. El mapa y CRUD operan por rutas de Web App. Airport e Itinerary carecen de IP pública y sus puertos internos se limitan por grupos de seguridad. |
| 5. Lambda y operación | Empaquetar el handler Python 3.12 y dependencias compatibles con Lambda. Crear el event source mapping tras migrar la base de notificaciones y verificar la topología. Habilitar alarmas y documentar recuperación. | Una creación genera una sola fila de historial aunque se entregue dos veces. Los fallos transitorios se reintentan y los mensajes inválidos quedan disponibles para diagnóstico. Se observa la salud del ALB, ECS, RDS, Lambda y cola. |
| 6. Automatización y disponibilidad | Evaluar GitHub Actions con OIDC y separar planificación, publicación y despliegue. Ajustar capacidad según métricas, presupuesto y objetivos de recuperación. | Los roles solo se asumen desde el repositorio y entorno previstos. La aplicación de cambios requiere autorización del entorno. Existe evidencia de recuperación y de reversión a un digest anterior. |

## Estado, identidad y datos

La raíz usa Terraform 1.10 o posterior y un backend S3 parcial con bloqueo nativo mediante `use_lockfile = true`. El módulo raíz de bootstrap declara el bucket con acceso público bloqueado, versionado, cifrado y TLS obligatorio. Consulta la [guía de inicialización y migración](bootstrap/README.md). Separar claves por entorno y roles por prefijo, idealmente en cuentas distintas para producción. El rol de despliegue puede leer y escribir su estado y leer, escribir y borrar su archivo de bloqueo. Limitar ListBucket al prefijo correspondiente. Separar el rol de plan, que necesita lectura de estado, acceso de lectura a los recursos y permisos sobre el bloqueo si se activa durante la planificación. Si se usa KMS, limitar sus permisos a la clave correspondiente. Verificar backend y recursos en el estado existente antes de migrar con `init -migrate-state` y conservar un respaldo protegido. Tratar estados, versiones y planes guardados como datos sensibles. Evitar su publicación como artefactos generales. [Backend S3 de Terraform](https://developer.hashicorp.com/terraform/language/backend/s3).

Para OIDC, restringir la confianza por audiencia y sujeto de GitHub, con entorno protegido para despliegue. Usar un rol de ejecución ECS separado de cada rol de tarea. Dar a Lambda permisos para su origen MQ, conectividad VPC, logs y los secretos específicos que necesita. Entregar URLs de servicios y referencias a secretos por configuración. En RDS usar la gestión de contraseña maestra de RDS y aprovisionar los usuarios de aplicación por un flujo privado. Definir y revisar cómo se entrega la credencial inicial de MQ, porque una contraseña enviada mediante un atributo persistido por el proveedor puede terminar en el estado aunque esté marcada como sensible.

En dev, evaluar una RDS PostgreSQL Single-AZ con dos bases y usuarios distintos, revocar CONNECT a PUBLIC en ambas y conceder a cada aplicación acceso solo a su base y sus objetos. La caída de la instancia afectaría a ambos servicios. Para separar fallos, escalado y restauraciones, usar dos instancias. Para tolerar caída de AZ, evaluar Multi-AZ por instancia independientemente. Ejecutar las migraciones con un rol separado, registrar su versión y serializar su ejecución. Revisar la creación de tablas al arrancar para que las migraciones sean la autoridad del esquema.

## Red por entorno

Configura el objeto network del ejemplo de variables con el CIDR y las zonas aprobadas. Conserva el orden de las zonas para no renumerar subredes existentes. En cada zona hay una subred pública para el ALB y NAT, una de aplicación con salida a internet mediante NAT y una de datos sin ruta por defecto. Las tareas usarán las subredes de aplicación sin IP pública. Reserva las subredes de datos para RDS y Amazon MQ. Configura por separado la conectividad del mapping de MQ y de la función Lambda.

El grupo de seguridad por defecto se declara sin reglas. Cada módulo de carga necesita grupos propios para autorizar solo sus flujos. Define la entrada pública del ALB, el acceso ALB → Web, las llamadas internas, AMQPS y PostgreSQL al conectar cada módulo. Con un NAT, la primera zona concentra la salida y las tareas de otras zonas pueden generar transferencia entre zonas. Activa nat_per_az para enviar el tráfico de cada subred de aplicación por un NAT de su zona. [Disponibilidad de NAT](https://docs.aws.amazon.com/vpc/latest/userguide/nat-gateway-basics.html).

## Datos y mensajería

Activa los objetos database y messaging del ejemplo después de configurar network. El broker de evaluación es RabbitMQ 4.3 en mq.m7g.medium. Para un clúster, configura tres zonas y selecciona una clase admitida para clúster. Usa la [guía de operaciones](operations/README.md) para crear bases y usuarios, aplicar SQL versionado y preparar la topología RabbitMQ.

## ECS y entrada HTTPS

El objeto compute habilita el clúster y el balanceador por entorno. Usa la [guía de ECS](containers/README.md) para preparar imágenes por digest, secretos y DNS. El ALB registra solo Web App e Itinerary conserva el acceso privado a PostgreSQL y Amazon MQ.

## Lambda y notificaciones

El objeto notification_worker crea la función, el mapping deshabilitado por defecto, la red privada y las alarmas. Sigue la [guía de notificaciones](notifications/README.md) para preparar la imagen, los secretos y la migración de cuarentena antes de activar el consumidor.

## Eventos y recuperación

Conservar el exchange `itineraries`, la clave `itinerary.created` y la cola `notifications`. Crear identidades separadas para bootstrap, publicación y consumo. Revisar qué declaraciones de topología hace hoy el código antes de retirar permisos de configuración. Preservar `ItineraryCreatedEvent` v1.0 con `data.itinerary_id`. El lector acepta `data.id` para mensajes antiguos. Lambda lee `rmqMessagesByQueue`, decodifica cada `data` de Base64 y valida el JSON de negocio. Mantener el adaptador de Compose y compartir la lógica de persistencia. Usar una restricción única con inserción atómica por `event_id`, y acordar cómo deduplicar cualquier mensaje histórico sin ese campo antes de habilitar el mapping. Nunca ejecutar los dos consumidores sobre la misma cola durante la transición. [Formato y entrega de Amazon MQ a Lambda](https://docs.aws.amazon.com/lambda/latest/dg/with-mq.html).

Empezar con lotes pequeños. El error de una invocación vuelve a entregar el lote completo. Para fallos transitorios, propagar el error y controlar conexiones PostgreSQL. Para un mensaje inválido, registrar evidencia sanitizada y conservarlo en una cuarentena duradera antes de darlo por procesado. Alarmar errores de Lambda, acumulación de cola, errores de publicación, falta de tareas saludables y espacio/conexiones de RDS. Correlacionar logs con `event_id` y el identificador de petición evitando volcar el cuerpo del evento. El mapping privado y la función tienen conectividad distinta. Para el mapping bajo demanda, diseñar endpoints de Lambda, STS y Secrets Manager o la ruta NAT soportada por AWS. La función requiere red propia hacia RDS y acceso a su secreto. [Red para el mapping de Amazon MQ](https://docs.aws.amazon.com/lambda/latest/dg/process-mq-messages-with-lambda.html).

Itinerary guarda y luego publica. Las confirmaciones de publicación y alarmas ayudan a detectar fallos, pero no cierran la ventana entre PostgreSQL y RabbitMQ. Definir un procedimiento explícito de reconciliación y republicación conservando la identidad del evento si está disponible. Si el requisito exige entrega recuperable desde la transacción, el equipo debe resolver el alcance de Transactional Outbox, actualmente Nivel 3. La arquitectura AWS incluye MQ por objetivo del despliegue. La ubicación del broker y de resiliencia en la rúbrica Base/Nivel 2 sigue pendiente.

## Costos de referencia

USD bajo demanda en us-east-1, 730 horas al mes, sin créditos ni impuestos. El entorno propuesto parte de una tarea por servicio, bajo tráfico, un NAT y una instancia compartida RDS. Las cifras se derivan de tarifas AWS publicadas.

| Componente | Supuesto | USD/mes |
|---|---|---:|
| ECS Fargate x86 | 3 tareas, 0.5 vCPU y 1 GB por tarea, incluida la capacidad para Service Connect, a USD 0.04048/vCPU-h y 0.004445/GB-h | 54.06 |
| ALB | USD 0.0225/h más uso de LCU a USD 0.008/LCU-h | 16.43 + uso |
| NAT zonal e IPv4 públicas | 1 NAT a 0.045/h y 3 IPv4 a 0.005/h cada una, incluidas 2 del ALB | 43.80 + tráfico |
| MQ de referencia | Un mq.m7g.large a 0.2734/h y 15 GiB a 0.10/GiB-mes, extrapolando la tarifa por nodo del ejemplo AWS | 201.08 |
| MQ de alta disponibilidad | Tres nodos mq.m7g.large y 45 GiB en total a las mismas tarifas | 603.25 |

El subtotal de ECS, ALB y NAT/IPv4 es aproximadamente USD 114.29/mes. Con el broker de referencia asciende a USD 315.37/mes antes de RDS y costos variables. AWS retiró mq.t3.micro para brokers RabbitMQ nuevos. Cotizar mq.m7g.medium de un nodo para evaluación antes de elegir clase. Completar la cotización con RDS PostgreSQL Single-AZ db.t4g.micro y 20 GiB gp3, ECR, Lambda, CloudWatch, Secrets Manager, S3, DNS, transferencia entre AZ y endpoints si se usan. Esas partidas no cuentan en el subtotal. Si el broker supera el presupuesto de desarrollo, mantener el flujo asíncrono de desarrollo en Compose y usar AWS para ventanas de integración presupuestadas.

Para mayor disponibilidad, distribuir al menos dos tareas de cada servicio entre zonas, evitar dependencia de un solo NAT, evaluar RDS Multi-AZ y pasar RabbitMQ a clúster. El MQ solo aumenta unos USD 402.17/mes en la comparación de tamaños iguales. Confirmar tasa regional, clase, motor, configuración y cargos en AWS Pricing Calculator antes del despliegue. [Tarifas de Fargate y ALB](https://docs.aws.amazon.com/solutions/latest/prebid-server-deployment-on-aws/cost1.html) · [VPC e IPv4](https://aws.amazon.com/vpc/pricing/) · [Tarifas de Amazon MQ](https://aws.amazon.com/amazon-mq/pricing/) · [Clases actuales de RabbitMQ](https://docs.aws.amazon.com/amazon-mq/latest/developer-guide/rmq-broker-instance-types.html) · [Precios de RDS PostgreSQL](https://aws.amazon.com/rds/postgresql/pricing/).

Antes de la fase 2, confirmar cuenta de desarrollo y estado ECR previo, presupuesto, región, CIDR, dominio/certificado y si dev necesita Amazon MQ permanente. Antes de habilitar el flujo de notificaciones, acordar los permisos de RabbitMQ, manejo de eventos perdidos y responsabilidades de migración. Las fases posteriores requieren verificación y autorización de cambios en AWS.
