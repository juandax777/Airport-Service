# Aprovisionamiento de datos y mensajería

Para `dev`, abre [AWS CloudShell en la VPC](https://docs.aws.amazon.com/cloudshell/latest/userguide/creating-vpc-environment.html). Selecciona `vpc_id` y una subred de `subnet_ids.app` de `terraform output -json network`. Asocia únicamente el grupo `client_security_groups.operations` de `terraform output -json data_services`. La subred usa NAT y el grupo permite salida HTTPS para obtener el código y los clientes, además del acceso privado a RDS y RabbitMQ. La sesión necesita permisos IAM de CloudShell en VPC y acceso a los secretos operativos correspondientes.

Obtén en la sesión el mismo commit que vas a desplegar, clonando el repositorio por HTTPS o usando un artefacto aprobado si es privado. Comprueba que tienes `psql` (en CloudShell puedes instalar el cliente con `sudo dnf install -y postgresql16`) y `python3`. La sesión es temporal. Guarda las credenciales en Secrets Manager, fuera del historial del shell y del repositorio. [Permisos IAM de CloudShell](https://docs.aws.amazon.com/cloudshell/latest/userguide/sec-auth-with-identities.html).

## PostgreSQL

1. Obtén la contraseña maestra del ARN de Secrets Manager que entrega RDS. Configura las variables libpq del ejecutor `PGHOST`, `PGPORT`, `PGUSER=platform_admin`, `PGSSLMODE=verify-full` y `PGSSLROOTCERT` con el [certificado oficial de RDS](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/UsingWithRDS.SSL.html). Usa un archivo de contraseñas temporal restringido o inyección segura.
2. Ejecuta desde la raíz del repo, en la instancia correspondiente a cada servicio:

   ```powershell
   psql -d postgres -v db=itineraries -f terraform/operations/bootstrap-postgres.sql
   psql -d postgres -v db=notifications -f terraform/operations/bootstrap-postgres.sql
   ```

   Cada ejecución crea la base y sus roles de aplicación y migración. Cuando se comparte RDS ambas se ejecutan sobre el host de la instancia `itinerary`. El script solicita las dos contraseñas interactivamente, incluso si los roles ya existían. Repetir con nuevas contraseñas equivale a rotarlas y requiere actualizar sus secretos. Guarda cada credencial de aplicación y migración por separado en Secrets Manager.
3. Instala psycopg 3 desde las dependencias existentes del proyecto en el ejecutor. Cambia `PGUSER` y la credencial al migrador correspondiente antes de cada comando.

   ```powershell
   python terraform/operations/migrate.py itineraries
   python terraform/operations/migrate.py notifications
   ```

   El ejecutor toma un bloqueo por base y guarda versión y hash en la misma transacción que los cambios SQL. Escribe migraciones nuevas en archivos numerados en orden ascendente, sin instrucciones que abran o cierren transacciones. Para nuevas secuencias u otros objetos, concede los permisos de aplicación requeridos explícitamente en su migración. Si ya hay tablas creadas por la aplicación, inspecciona esquema y propietarios antes de usar el ejecutor. El SQL inicial contiene CREATE TABLE IF NOT EXISTS y no verifica que una tabla preexistente coincida con el esquema migrado.
4. Para ECS, configura `DATABASE_AUTO_CREATE=false` y el secreto `DATABASE_URL` con el usuario `itineraries_app` y verificación TLS. La notificación AWS usará `notifications_app`. El rol de aplicación no recibe permisos de DDL ni acceso al registro de migraciones.

El ejemplo usa PostgreSQL 16 en una instancia. Puedes activar `separate_instances` para crear la segunda. Para un entorno existente, crea el destino, migra y verifica los datos, cambia la conexión de notificaciones y revoca sus accesos al origen antes de retirar su copia anterior. La variable por sí sola no mueve ni elimina datos.

## RabbitMQ

1. Usa `MQ_CONSOLE_URL` del output (HTTPS en puerto 443), `MQ_ADMIN_USER` y `MQ_ADMIN_PASSWORD` inyectados mediante el almacén de secretos del operador. Ejecuta `python terraform/operations/bootstrap-rabbitmq.py` desde el ejecutor privado. Crea el exchange topic durable `itineraries`, la cola quorum durable `notifications` y la ruta `itinerary.created` en el vhost `/`. Si existe una cola de otro tipo, resuelve su migración antes de reintentar.
2. Crea usuarios distintos de publicación y consumo en la consola privada o API de gestión. Usa expresiones regulares ancladas de permisos para el vhost.

   | Usuario | Configure | Write | Read |
   |---|---|---|---|
   | Publicador Itinerary | `^$` | `^itineraries$` | `^$` |
   | Consumidor Lambda | `^$` | `^$` | `^notifications$` |

   Guarda la URL AMQPS del publicador, con usuario y contraseña codificados para URL, en su propio secreto. Para el futuro mapping Lambda reserva otro secreto JSON con `username` y `password`. Configura `RABBITMQ_DECLARE_TOPOLOGY=false` en Itinerary AWS para reutilizar el exchange preparado. El consumidor en contenedor de Compose sigue declarando la topología local.
3. Antes de habilitar escrituras en ECS, verifica que el binding exista. El módulo de notificaciones crea el mapping y los endpoints privados cuando se configura `notification_worker`. En RabbitMQ 4 las métricas de cola individuales se consultan mediante la API de gestión. [Conectividad de MQ](https://docs.aws.amazon.com/amazon-mq/latest/developer-guide/working-with-rabbitmq.html) · [RabbitMQ 4 en Amazon MQ](https://docs.aws.amazon.com/amazon-mq/latest/developer-guide/rabbitmq-4.html).

El proveedor AWS 5 requiere la contraseña inicial de MQ en el bloque de usuario y la conserva en el estado y planes guardados. Inyecta únicamente una credencial de bootstrap mediante `TF_VAR_mq_admin_password`. Restringe el acceso al estado y sus versiones, evita guardar o distribuir el plan con ese valor y rota la credencial inicial en RabbitMQ una vez habilitado el acceso operativo. Cambiar la variable posteriormente no rota un usuario RabbitMQ. [Recurso MQ del proveedor AWS](https://registry.terraform.io/providers/hashicorp/aws/5.100.0/docs/resources/mq_broker).
