# Contexto del proyecto

## Producto

**Sistema de Itinerarios Personales** permite consultar aeropuertos colombianos, verlos en un mapa, gestionar itinerarios y procesar una notificación de creación mediante eventos.

## Arquitectura actual

- `services/airport_service`: FastAPI consulta API Colombia y adapta la respuesta a un modelo interno. El frontend no debe consultar directamente el proveedor externo.
- `services/itinerary_service`: FastAPI valida aeropuertos a través de Airport Service, expone el CRUD y publica `ItineraryCreatedEvent`.
- `services/notification_service`: consume el evento de RabbitMQ y guarda el resultado simulado del procesamiento.
- `services/web_app`: aplicación web FastAPI con plantillas Jinja y JavaScript/CSS; consume los servicios internos.
- `rabbitmq`: transporte asíncrono; el exchange `itineraries` publica con routing key `itinerary.created` y la cola `notifications` lo consume.
- Cada servicio con persistencia tiene su base de datos aislada. `docker-compose.yml` define el entorno local.
- `terraform/` contiene infraestructura AWS preparada; el flujo local no despliega recursos cloud.

## Tecnologías y convenciones

- Python 3.12, FastAPI, Pydantic, SQLAlchemy, PostgreSQL, RabbitMQ, Docker Compose.
- Frontend servido por FastAPI, Jinja2, JavaScript y Plotly JS.
- Configuración y dependencias compartidas: `pyproject.toml`; los contenedores instalan desde `services/*/requirements.txt`.
- Calidad: Ruff, pytest y CI en `.github/workflows/ci.yml`.
- Contrato de eventos: `contracts/asyncapi.yaml`.

## Fuentes de verdad

1. `docs/requisitos.md` y `docs/historias-de-usuario.md` definen alcance, identificadores y criterios de aceptación.
2. `contracts/asyncapi.yaml` define el contrato asíncrono.
3. El código y los workflows describen el comportamiento implementado.
4. `README.md`, `docs/MANUAL_EJECUCION.md` y `docs/DEVELOPMENT.md` documentan uso y desarrollo.

Si estas fuentes discrepan, describe la contradicción y evita inventar una decisión de producto. El README registra pendientes sobre Outbox, el alcance de notificaciones y el nivel mínimo requerido para mensajería/resiliencia.

## Contrato de evento vigente

`ItineraryCreatedEvent` usa `data.itinerary_id` como campo canónico, según el productor y `contracts/asyncapi.yaml`. Notification Service acepta también `data.id` únicamente como compatibilidad con mensajes antiguos que pudieran quedar en la cola. Los cambios nuevos deben conservar el formato canónico y actualizar juntos productor, consumidor, contrato y documentación.

## Límites del alcance

- No asumir que funcionalidades de Nivel 2 o Nivel 3 ya están implementadas solo porque figuren en requisitos.
- No reemplazar el proveedor API Colombia, RabbitMQ ni contratos sin una necesidad ligada a un requisito o una decisión explícita.
- No introducir una llamada directa desde el frontend a API Colombia.
