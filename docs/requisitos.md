# Requisitos del Sistema de Itinerarios Personales

Este documento es la referencia trazable de requisitos adoptada por el proyecto. La descripción detallada del alcance se complementa con los criterios de aceptación de [`historias-de-usuario.md`](historias-de-usuario.md).

## Requisitos funcionales

| ID | Requisito | Descripción | Prioridad | Nivel |
|---|---|---|---|---|
| RF-01 | Consultar aeropuertos colombianos | Airport Service consulta API Colombia; el frontend nunca accede directamente a la fuente externa. | Alta | Base |
| RF-02 | Consultar aeropuerto por ID | Airport Service expone un endpoint REST para recuperar un aeropuerto específico. | Alta | Base |
| RF-03 | Adaptar respuesta externa | La respuesta externa se traduce a un modelo interno antes de entregarse a otros componentes. | Alta | Base |
| RF-04 | Transformar datos para Plotly | Airport Service prepara la información geográfica requerida por Plotly JS. | Alta | Base |
| RF-05 | Visualizar aeropuertos | El frontend muestra un mapa interactivo y, como mínimo, un aeropuerto obtenido de Airport Service. | Alta | Base |
| RF-06 | Crear itinerario | El usuario registra nombre, salida, llegada, fecha y duración en minutos. | Alta | Base |
| RF-07 | Consultar itinerarios | Itinerary Service devuelve los itinerarios almacenados. | Alta | Base |
| RF-08 | Consultar itinerario por ID | El sistema devuelve un itinerario específico mediante su identificador. | Alta | Base |
| RF-09 | Actualizar itinerario | El usuario modifica un itinerario; los aeropuertos cambiados se validan nuevamente. | Alta | Base |
| RF-10 | Eliminar itinerario | El sistema elimina un itinerario existente. | Alta | Base |
| RF-11 | Validar salida | La salida debe existir antes de crear o actualizar. | Alta | Base |
| RF-12 | Validar llegada | La llegada debe existir antes de crear o actualizar. | Alta | Base |
| RF-13 | Persistir itinerarios | Itinerary Service guarda los viajes en su base relacional propia. | Alta | Base |
| RF-14 | Publicar evento | Una creación correcta produce `ItineraryCreatedEvent` de forma asíncrona. | Alta | Base/N2 por confirmar |
| RF-15 | Procesar notificación | La recepción del evento activa el componente de notificaciones. | Alta | Arquitectura |
| RF-16 | Simular envío | `SendNotificationFunction` simula el correo o registra una acción equivalente. | Alta | Arquitectura |
| RF-17 | Registrar historial | El componente de notificaciones persiste su historial de procesamiento. | Alta | Arquitectura |
| RF-18 | Generar reporte | `GenerateItineraryReportFunction` consolida métricas bajo demanda sin sobrecargar los servicios principales. | Baja | Opcional |

## Datos y persistencia

| ID | Requisito | Nivel |
|---|---|---|
| RD-01 | Usar una base relacional: SQLite, PostgreSQL o MySQL. | Base |
| RD-02 | Mantener una base de datos independiente por servicio. | Base |
| RD-03 | Versionar el esquema mediante Alembic, Flyway, Liquibase o equivalente. | Base |
| RD-04 | Incluir nombre, salida, llegada, fecha y duración en el modelo de itinerario. | Base |
| RD-05 | Mantener una persistencia propia para el historial de notificaciones. | Arquitectura |
| RD-06 | Registrar evento e itinerario en la misma transacción mediante Outbox. | Nivel 3 |

## Integración

| ID | Requisito | Nivel |
|---|---|---|
| RI-01 | Itinerary Service valida aeropuertos mediante HTTP hacia Airport Service. | Base |
| RI-02 | Soportar comunicación asíncrona para eventos de itinerarios. | Base/N2 por confirmar |
| RI-03 | Utilizar RabbitMQ o Kafka. | Nivel 2 por confirmar |
| RI-04 | Usar una cola o tópico dedicado a itinerarios. | Nivel 2 |
| RI-05 | Documentar mensajes, canales y protocolo con AsyncAPI. | Nivel 2 |
| RI-06 | Proporcionar un API Gateway/BFF. | Nivel 2 |
| RI-07 | Enrutar desde el Gateway sin lógica de negocio. | Nivel 2 |
| RI-08 | Aplicar rate limiting. | Nivel 2 |
| RI-09 | Propagar JWT hacia los servicios internos. | Nivel 2 |
| RI-10 | Permitir gRPC/Protobuf entre Itinerary Service y Airport Service. | Nivel 3 |

## Requisitos no funcionales

| ID | Requisito | Nivel |
|---|---|---|
| RNF-01 | Separar las responsabilidades por dominio. | Base |
| RNF-02 | Permitir desarrollo, despliegue y mantenimiento independiente de servicios. | Base |
| RNF-03 | Desacoplar el frontend de API Colombia. | Base |
| RNF-04 | Responder con códigos HTTP y errores consistentes. | Base |
| RNF-05 | Mantener una estructura clara y coherente del proyecto. | Base |
| RNF-06 | Soportar la concurrencia propia de un sistema distribuido. | General |
| RNF-07 | Evitar que una falla externa derribe la solución completa. | Nivel 2 |

## Arquitectura

| ID | Requisito | Nivel |
|---|---|---|
| RA-01 | Implementar Airport Service e Itinerary Service como microservicios. | Base |
| RA-02 | Aplicar arquitectura hexagonal. | Base |
| RA-03 | Implementar formalmente Puerto y Adapter para API Colombia. | Base |
| RA-04 | Definir contratos con interfaces o clases abstractas. | Base |
| RA-05 | Documentar contextos delimitados y lenguaje ubicuo. | Base |
| RA-06 | Separar dominio de base de datos, APIs, broker e infraestructura. | Base |
| RA-07 | Desacoplar acciones posteriores mediante eventos de integración. | Arquitectura |
| RA-08 | Ejecutar notificaciones y reportes como funciones FaaS. | Arquitectura |
| RA-09 | Documentar si Aeropuerto es referencia de valor o agregado completo. | Documentación |
| RA-10 | Diferenciar eventos de dominio y de integración. | Documentación |

## Resiliencia, seguridad y observabilidad

| Grupo | IDs | Contenido | Nivel principal |
|---|---|---|---|
| Resiliencia | RR-01 a RR-05 | Timeout, Circuit Breaker, backoff con jitter, Redis e invalidación. | Nivel 2 |
| Resiliencia avanzada | RR-06 a RR-07 | Bulkhead y Chaos Engineering. | Nivel 3 |
| Seguridad | RS-01 a RS-02 | JWT y propagación segura. | Nivel 2 |
| Seguridad avanzada | RS-03 a RS-04 | mTLS/OAuth2 S2S y Vault/Config Server. | Nivel 3 |
| Observabilidad | ROB-01 a ROB-02 | Logs JSON, `trace_id` y `span_id`. | Base |
| Observabilidad avanzada | ROB-03 a ROB-06 | Jaeger, Prometheus, Grafana y alertas. | Nivel 2/3 |

## Infraestructura y pruebas

| Grupo | IDs | Contenido |
|---|---|---|
| Infraestructura | RINF-01 a RINF-05 | Docker, Compose, simulación FaaS, Pydantic y Swagger. |
| Infraestructura avanzada | RINF-06 a RINF-10 | CI/CD, Kubernetes, probes, versionamiento y paginación. |
| Pruebas | RP-01 | Cobertura unitaria mínima del 70 %. |
| Pruebas Nivel 2 | RP-02 a RP-04 | E2E, Testcontainers y demostración del Circuit Breaker. |
| Pruebas Nivel 3 | RP-05 | Contract Testing con Pact o equivalente. |

## Entregables

La entrega debe contener código en Git, README, requisitos, historias de usuario, backlog en Jira, documento de arquitectura, diagramas, instrucciones de ejecución, evidencias del nivel alcanzado y tabla de autoevaluación. Los requisitos de entrega se identifican como RDO-01 a RDO-19 en el documento fuente.

## Observaciones pendientes

1. Outbox aparece como mecanismo arquitectónico general y también como Nivel 3; se planifica como Nivel 3 hasta confirmación.
2. Las notificaciones aparecen como FaaS y como tercer microservicio; se toma FaaS como referencia inicial.
3. El flujo asíncrono parece central, pero broker, Redis y mecanismos de resiliencia aparecen en Nivel 2; debe validarse el mínimo evaluable.
