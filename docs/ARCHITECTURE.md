# Documento de arquitectura

## 1. Propósito y alcance

Sistema de Itinerarios Personales consulta aeropuertos colombianos, permite visualizarlos y gestionar itinerarios, y procesa una notificación después de crear un itinerario. Este documento describe la arquitectura implementada para desarrollo local con Docker Compose. La infraestructura AWS que aparece en `terraform/` es una preparación incompleta, no un entorno desplegado.

## 2. Vista de contexto y contenedores

La aplicación web sirve la interfaz y actúa como fachada de las APIs internas. Airport Service integra el proveedor externo y entrega un modelo interno. Itinerary Service valida aeropuertos, persiste itinerarios y publica eventos. Notification Service consume esos eventos y registra el resultado simulado.

Diagrama editable: [arquitectura de servicios y despliegue local](diagrams/system-architecture.drawio).

| Componente | Responsabilidad | Interfaz o tecnología |
|---|---|---|
| Web App | Interfaz web y proxy hacia los servicios internos. | FastAPI, Jinja2, JavaScript, HTTP |
| Airport Service | Adaptar y exponer aeropuertos de API Colombia. | FastAPI, HTTP externo |
| Itinerary Service | Validar y gestionar itinerarios; publicar eventos. | FastAPI, HTTP, PostgreSQL, RabbitMQ |
| Notification Service | Consumir eventos y registrar notificaciones simuladas. | Consumidor RabbitMQ, PostgreSQL |
| RabbitMQ | Entrega asíncrona de `ItineraryCreatedEvent`. | Exchange `itineraries`, routing key `itinerary.created`, cola `notifications` |
| Bases de datos | Persistencia independiente para itinerarios e historial de notificaciones. | PostgreSQL; una base por servicio |
| API Colombia | Fuente externa de datos de aeropuertos. | HTTP/REST |

## 3. Estructura hexagonal por servicio

Los adaptadores de entrada traducen HTTP o mensajes al modelo de aplicación. Los casos de uso dependen de puertos, y los adaptadores de infraestructura implementan esos puertos para HTTP, PostgreSQL o RabbitMQ. El dominio no debe importar FastAPI, SQLAlchemy, `httpx` ni `aio-pika`.

Diagrama editable: [capas y adaptadores de los servicios](diagrams/service-layers.drawio).

| Servicio | Entrada | Aplicación / dominio | Puertos y adaptadores de salida |
|---|---|---|---|
| Web App | Rutas FastAPI | Proxy de solicitudes de interfaz | `ServiceGateway`; gateway HTTP para Airport e Itinerary Service |
| Airport Service | API FastAPI | Casos de uso de catálogo y modelo `Airport` | Puerto de catálogo; adaptador HTTP para API Colombia |
| Itinerary Service | API FastAPI | Casos de uso y entidad `Itinerary` | Repositorio SQL, cliente HTTP de aeropuertos y publicador RabbitMQ |
| Notification Service | Consumidor RabbitMQ | Caso de uso de procesamiento y modelo `Notification` | Repositorio SQL y adaptador de mensajería |

Los paquetes concretos pueden consultarse bajo `services/<servicio>/app/`. La estructura debe mantenerse alineada con el código y los tests.

## 4. Flujos de integración

### Consulta y creación

1. El navegador solicita datos a Web App.
2. Web App reenvía las llamadas a Airport Service o Itinerary Service.
3. Itinerary Service valida los aeropuertos de salida y llegada mediante HTTP con Airport Service.
4. Itinerary Service persiste el itinerario en su propia base PostgreSQL.
5. Después de guardarlo, publica `ItineraryCreatedEvent` en RabbitMQ.
6. Notification Service consume el evento y registra el procesamiento en su base propia.

Diagrama editable: [flujo de creación de itinerario y notificación](diagrams/itinerary-event-flow.drawio).

El contrato canónico está en `contracts/asyncapi.yaml`. El identificador se representa como `data.itinerary_id`; productor y consumidor deben usar el mismo nombre.

## 5. Datos y persistencia

Itinerary Service es propietario de la entidad `Itinerary` y de su tabla `itineraries`. Notification Service es propietario de `Notification` y de su tabla `notifications`. No hay relaciones de base de datos entre servicios: se intercambian identificadores mediante HTTP y eventos.

Diagrama editable: [modelo de datos por servicio](diagrams/data-model.drawio).

Docker Compose inicia dos contenedores PostgreSQL con volúmenes separados. Actualmente las tablas se crean desde los modelos SQLAlchemy al iniciar cada servicio. Los archivos SQL en `services/*/migrations/` existen, pero no se ejecutan; conviene elegir un único mecanismo de migración y usarlo para futuras versiones del esquema.

## 6. Despliegue y DevOps

- Desarrollo local: `docker-compose.yml` inicia los cuatro componentes de aplicación, RabbitMQ y las dos bases de datos.
- Cada componente de aplicación tiene su propio Dockerfile. Un Compose de raíz permite iniciar el sistema integrado y respeta las dependencias entre servicios.
- CI en `.github/workflows/ci.yml` instala dependencias, ejecuta Ruff y pytest, valida Compose, construye imágenes y escanea vulnerabilidades con Trivy.
- k6 proporciona un escenario de carga manual, de solo lectura y dirigido a localhost; véase `tests/load/README.md`.
- El análisis SonarQube es opcional en CI y requiere configurar las variables/secretos de GitHub descritos en `docs/GITHUB_REPOSITORY.md`.
- `.github/workflows/release.yml` publica imágenes de backend en Amazon ECR cuando se habilita. No despliega aún la aplicación en ECS/Lambda. `terraform/` crea actualmente repositorios ECR; los demás recursos de AWS están pendientes de aprobación y definición.
- El repositorio documenta ramas cortas y Pull Requests en `CONTRIBUTING.md`. La protección de `main`, los checks requeridos y las revisiones se configuran en GitHub; no se pueden garantizar solo con archivos del repositorio.
- El README y las plantillas contemplan Jira, pero el tablero y su backlog viven fuera de Git. Relaciona cada tarea/PR con su ID de Jira, HU o RF.

## 7. Documentación de interfaces

- Swagger/OpenAPI de Airport Service: `http://localhost:8001/docs`.
- Swagger/OpenAPI de Itinerary Service: `http://localhost:8002/docs`.
- Contrato asíncrono: `contracts/asyncapi.yaml`.
- Requisitos e historias: `docs/requisitos.md` y `docs/historias-de-usuario.md`.

## 8. Decisiones y límites conocidos

- API Colombia es un proveedor externo; su formato se traduce dentro de Airport Service mediante un Adapter.
- Las bases de datos permanecen aisladas por servicio.
- Notificaciones se implementan actualmente como un consumidor en contenedor. La opción FaaS en AWS está descrita como objetivo, no como despliegue existente.
- Outbox, autenticación JWT, resiliencia avanzada y observabilidad distribuida pertenecen a decisiones o niveles aún pendientes según `README.md` y `docs/requisitos.md`.
- Cualquier cambio en HTTP o eventos debe actualizar el contrato, sus productores/consumidores y la documentación afectada en el mismo cambio.

## 9. Diagramas interactivos Archify

Se agregan estas vistas interactivas en HTML. Las fuentes JSON están junto a cada diagrama; los diagramas editables `.drawio` existentes se conservan.

| Vista | Diagrama interactivo | Fuente Archify |
|---|---|---|
| Arquitectura local del sistema | [Abrir HTML](../.archify/architecture-system-overview-20261009-175300/system-overview.html) | [candidate.json](../.archify/architecture-system-overview-20261009-175300/candidate.json) |
| Capas hexagonales de Itinerary Service | [Abrir HTML](../.archify/architecture-hexagonal-itinerary-20261009-174334/hexagonal-itinerary.html) | [candidate.json](../.archify/architecture-hexagonal-itinerary-20261009-174334/candidate.json) |
| Secuencia de creación y notificación | [Abrir HTML](../.archify/sequence-itinerary-creation-20261009-173423/itinerary-creation.html) | [candidate.json](../.archify/sequence-itinerary-creation-20261009-173423/candidate.json) |
| Flujo de datos del itinerario | [Abrir HTML](../.archify/dataflow-itinerary-data-20261009-173423/itinerary-data.html) | [candidate.json](../.archify/dataflow-itinerary-data-20261009-173423/candidate.json) |
| CI y publicación opcional en ECR | [Abrir HTML](../.archify/workflow-ci-publication-20261009-173423/ci-publication.html) | [candidate.json](../.archify/workflow-ci-publication-20261009-173423/candidate.json) |
