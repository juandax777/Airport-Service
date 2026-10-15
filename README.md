# Sistema de Itinerarios Personales

Sistema distribuido para consultar aeropuertos colombianos, visualizarlos en un mapa, gestionar itinerarios y generar notificaciones de manera asíncrona.

## Inicio rápido

```powershell
Copy-Item .env.example .env
docker compose up --build
```

Abre `http://localhost:8000` para usar la aplicación web. Swagger queda disponible en `http://localhost:8001/docs` y `http://localhost:8002/docs`.

- Ejecución completa: [`docs/MANUAL_EJECUCION.md`](docs/MANUAL_EJECUCION.md).
- Arquitectura y diagramas editables: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).
- Prueba de carga local: [`tests/load/README.md`](tests/load/README.md).
- Publicación y organización en GitHub: [`docs/GITHUB_REPOSITORY.md`](docs/GITHUB_REPOSITORY.md).
- Reglas de colaboración: [`CONTRIBUTING.md`](CONTRIBUTING.md).

## Base oficial del proyecto

Este proyecto toma como fuentes de alcance y planificación:

1. [`docs/requisitos.md`](docs/requisitos.md), derivado de `Documento_Requisitos_Sistema_Itinerarios_Personales.docx.md`.
2. [`docs/historias-de-usuario.md`](docs/historias-de-usuario.md), derivado de `Historias_de_Usuario_Sistema_Itinerarios_Personales.docx.md`.

Los identificadores, prioridades, niveles y criterios de aceptación de esos documentos prevalecen sobre versiones anteriores del README. Los puntos contradictorios quedan registrados en la sección [Decisiones pendientes](#decisiones-pendientes).

## Objetivos

- Consultar aeropuertos colombianos a través de Airport Service.
- Desacoplar el sistema de API Colombia mediante puertos y adaptadores.
- Mostrar aeropuertos en un mapa interactivo con Plotly JS.
- Crear, consultar, actualizar y eliminar itinerarios.
- Validar salida y llegada antes de persistir un itinerario.
- Publicar y procesar `ItineraryCreatedEvent` de forma asíncrona.
- Procesar eventos y registrar notificaciones con un consumidor local en contenedor; el despliegue FaaS en AWS aún no está implementado.

## Alcance por nivel

### Base

- Airport Service e Itinerary Service independientes.
- Arquitectura hexagonal, DDD básico y patrón Adapter.
- Consulta de aeropuertos y transformación para Plotly JS.
- CRUD completo de itinerarios con validación mediante HTTP.
- Base de datos relacional independiente por servicio. Hay scripts SQL de migración versionados, pero aún no se ejecutan automáticamente.
- Logs JSON con identificadores de correlación.
- Swagger, frontend básico, Docker y Docker Compose.
- Cobertura unitaria mínima del 70 %.

### Nivel 2

- RabbitMQ o Kafka y contrato AsyncAPI.
- API Gateway/BFF, rate limiting y propagación de JWT.
- Redis, timeout, reintentos y Circuit Breaker.
- OpenTelemetry y Jaeger.
- Pruebas E2E con Testcontainers y demostración de resiliencia.

### Nivel 3

- Transactional Outbox, gRPC y Protobuf.
- Seguridad S2S y gestión dinámica de secretos.
- Bulkhead, Chaos Engineering y alertas operativas.
- CI/CD, Kubernetes, Contract Testing, versionamiento y paginación.

## Componentes

| Componente | Responsabilidad |
|---|---|
| Frontend | Mostrar el mapa y permitir la gestión de itinerarios. |
| API Gateway/BFF | Enrutar, limitar solicitudes y propagar identidad sin lógica de negocio. |
| Airport Service | Consultar API Colombia, adaptar la respuesta y entregar aeropuertos. |
| Itinerary Service | Validar aeropuertos, gestionar itinerarios y publicar eventos. |
| Broker | Transportar eventos de itinerarios. |
| SendNotificationFunction | Procesar eventos y registrar notificaciones. |
| GenerateItineraryReportFunction | Generar métricas bajo demanda; es opcional. |

## Requisitos funcionales

| ID | Requisito | Prioridad | Nivel |
|---|---|---|---|
| RF-01 | Consultar aeropuertos colombianos mediante Airport Service y API Colombia. | Alta | Base |
| RF-02 | Consultar un aeropuerto por identificador mediante REST. | Alta | Base |
| RF-03 | Adaptar la respuesta externa a un modelo de dominio interno. | Alta | Base |
| RF-04 | Transformar datos al formato requerido por Plotly JS. | Alta | Base |
| RF-05 | Visualizar aeropuertos en un mapa consumiendo Airport Service. | Alta | Base |
| RF-06 | Crear un itinerario con la información mínima requerida. | Alta | Base |
| RF-07 | Consultar todos los itinerarios almacenados. | Alta | Base |
| RF-08 | Consultar un itinerario por identificador. | Alta | Base |
| RF-09 | Actualizar un itinerario y revalidar los aeropuertos modificados. | Alta | Base |
| RF-10 | Eliminar un itinerario existente. | Alta | Base |
| RF-11 | Validar el aeropuerto de salida antes de crear o actualizar. | Alta | Base |
| RF-12 | Validar el aeropuerto de llegada antes de crear o actualizar. | Alta | Base |
| RF-13 | Persistir itinerarios en la base de datos propia del servicio. | Alta | Base |
| RF-14 | Publicar `ItineraryCreatedEvent` después de una creación correcta. | Alta | Base/Nivel 2 por confirmar |
| RF-15 | Activar el procesamiento de notificaciones al recibir el evento. | Alta | Eventos/Serverless |
| RF-16 | Simular el envío o registro equivalente de una notificación. | Alta | Eventos/Serverless |
| RF-17 | Guardar el historial del procesamiento de notificaciones. | Alta | Eventos/Serverless |
| RF-18 | Generar un reporte de métricas bajo demanda. | Baja | Opcional |

## Modelo mínimo de itinerario

| Campo | Regla |
|---|---|
| `id` | Identificador único generado por el sistema. |
| `user_name` | Nombre obligatorio del usuario. |
| `departure_airport_id` | ID obligatorio que debe existir en Airport Service. |
| `arrival_airport_id` | ID obligatorio que debe existir en Airport Service. |
| `travel_date` | Fecha de viaje válida. |
| `duration_minutes` | Duración válida expresada en minutos. |

## Requisitos complementarios

### Datos e integración

| Grupo | Requisitos adoptados |
|---|---|
| RD-01 a RD-06 | Base relacional, datos aislados por servicio, migraciones, modelo mínimo, historial propio y Outbox de Nivel 3. |
| RI-01 a RI-10 | HTTP interno, eventos asíncronos, broker, canal dedicado, AsyncAPI, Gateway, rate limiting, JWT y gRPC de Nivel 3. |

### No funcionales y arquitectura

| Grupo | Requisitos adoptados |
|---|---|
| RNF-01 a RNF-07 | Responsabilidades separadas, independencia, desacoplamiento, errores HTTP, organización, concurrencia y resiliencia. |
| RA-01 a RA-10 | Microservicios, arquitectura hexagonal, Adapter, interfaces, DDD, eventos, Serverless y documentación de decisiones de dominio. |
| RR-01 a RR-07 | Timeout, Circuit Breaker, backoff con jitter, Redis, invalidación, Bulkhead y Chaos Engineering. |
| RS-01 a RS-04 | JWT, propagación segura, seguridad S2S y gestión de secretos. |
| ROB-01 a ROB-06 | Logs JSON, correlación, trazas, métricas, paneles y alertas. |
| RINF-01 a RINF-10 | Docker, Compose, FaaS local, Pydantic, Swagger, CI/CD, Kubernetes, probes, versionamiento y paginación. |
| RP-01 a RP-05 | Cobertura mínima del 70 %, E2E, Testcontainers, prueba de resiliencia y Contract Testing. |

API Colombia es el sistema externo o *adaptee*. El Adapter es la implementación interna de Airport Service que traduce la API externa al modelo de dominio.

## Historias de usuario y trazabilidad

| Épica | Historia | Requisitos | Nivel |
|---|---|---|---|
| EP-01 Gestión de Aeropuertos | HU-01 Consultar aeropuertos disponibles | RF-01, RF-03 | Base |
| EP-01 Gestión de Aeropuertos | HU-02 Consultar aeropuerto por ID | RF-02 | Base |
| EP-02 Visualización | HU-03 Visualizar aeropuertos en mapa | RF-04, RF-05 | Base |
| EP-03 Gestión de Itinerarios | HU-04 Crear itinerario | RF-06, RF-11, RF-12, RF-13 | Base |
| EP-03 Gestión de Itinerarios | HU-05 Consultar itinerarios | RF-07 | Base |
| EP-03 Gestión de Itinerarios | HU-06 Consultar detalle | RF-08 | Base |
| EP-03 Gestión de Itinerarios | HU-07 Actualizar itinerario | RF-09, RF-11, RF-12 | Base |
| EP-03 Gestión de Itinerarios | HU-08 Eliminar itinerario | RF-10 | Base |
| EP-04 Notificaciones | HU-09 Generar notificación | RF-14 a RF-17 | Eventos/Serverless |
| EP-05 Reportes | HU-10 Generar reporte | RF-18 | Opcional |

Los criterios de aceptación detallados de las historias son condiciones de entrega. Los elementos puramente técnicos se gestionarán como historias técnicas, *enablers* o tareas del backlog, no como necesidades ficticias del usuario final.

## Entregables

- Código fuente completo en un repositorio Git.
- README con arquitectura e instrucciones de ejecución.
- Documento de requisitos e historias de usuario trazables.
- Backlog mantenido en Jira.
- Documento de arquitectura.
- Diagramas de componentes, clases, datos, secuencia y despliegue.
- Explicación de DDD, Adapter, eventos y flujo asíncrono.
- Evidencia del mapa y de la creación de un itinerario con su notificación.
- Evidencias adicionales correspondientes al nivel alcanzado.
- Tabla de autoevaluación.

## Decisiones pendientes

1. **Transactional Outbox:** la arquitectura lo propone para publicar eventos, pero la rúbrica lo ubica en Nivel 3. Se tratará como Nivel 3 hasta confirmación.
2. **Notificaciones:** el alcance principal exige funciones Serverless, mientras que otra sección menciona un tercer microservicio. La referencia inicial será FaaS local.
3. **Broker y resiliencia:** el flujo principal requiere comunicación asíncrona, pero broker, Redis, reintentos y Circuit Breaker aparecen como Nivel 2. Esta dependencia debe validarse antes de cerrar el alcance base.

## Definición de terminado

Una historia se considera terminada cuando:

- Cumple todos sus criterios de aceptación.
- Conserva la separación entre dominio e infraestructura.
- Maneja los errores esperados de forma consistente.
- Incluye las pruebas automatizadas pertinentes.
- Mantiene una cobertura global mínima del 70 %.
- Actualiza Swagger, AsyncAPI o la documentación afectada.
- Funciona dentro del entorno Docker Compose.
- No introduce secretos ni configuración sensible en el repositorio.
