# Historias de Usuario del Sistema de Itinerarios Personales

Las siguientes historias y criterios de aceptación son la base del backlog funcional.

## Épicas

| Épica | Historias | Alcance |
|---|---|---|
| EP-01 Gestión de Aeropuertos | HU-01, HU-02 | Base |
| EP-02 Visualización de Aeropuertos | HU-03 | Base |
| EP-03 Gestión de Itinerarios | HU-04 a HU-08 | Base |
| EP-04 Notificaciones | HU-09 | Eventos/Serverless |
| EP-05 Reportes | HU-10 | Opcional |

## HU-01 Consultar aeropuertos disponibles

**Como** usuario, **quiero** consultar los aeropuertos colombianos disponibles, **para** conocer cuáles puedo utilizar al planificar mi itinerario.

**Requisitos:** RF-01, RF-03. **Prioridad:** alta. **Nivel:** base.

### Criterios de aceptación

- El sistema muestra los aeropuertos obtenidos correctamente.
- Los datos provienen de Airport Service, nunca directamente de API Colombia.
- Airport Service adapta los datos al modelo interno.
- Una falla externa produce una respuesta controlada.

## HU-02 Consultar aeropuerto por identificador

**Como** usuario, **quiero** consultar un aeropuerto específico, **para** conocer los datos del aeropuerto que podría usar.

**Requisito:** RF-02. **Prioridad:** alta. **Nivel:** base.

### Criterios de aceptación

- Un identificador válido devuelve el aeropuerto correspondiente.
- Un aeropuerto inexistente produce una respuesta de recurso no encontrado.
- La consulta usa el endpoint de Airport Service.
- La respuesta utiliza el modelo interno.

## HU-03 Visualizar aeropuertos en un mapa

**Como** usuario, **quiero** visualizar aeropuertos en un mapa interactivo, **para** identificar fácilmente su ubicación.

**Requisitos:** RF-04, RF-05. **Prioridad:** alta. **Nivel:** base.

### Criterios de aceptación

- El frontend muestra un mapa interactivo con Plotly JS.
- El mapa consume Airport Service.
- Se visualiza correctamente al menos un aeropuerto.
- La información geográfica llega en el formato requerido por Plotly.
- El frontend no consulta directamente API Colombia.

## HU-04 Crear itinerario

**Como** usuario, **quiero** crear un itinerario con la información básica del viaje, **para** organizar mi recorrido.

**Requisitos:** RF-06, RF-11, RF-12, RF-13. **Prioridad:** alta. **Nivel:** base.

### Criterios de aceptación

- El usuario ingresa nombre, salida, llegada, fecha y duración en minutos.
- Salida y llegada se validan antes de guardar.
- Si algún aeropuerto no existe, no se persiste el itinerario.
- Si todos los datos son válidos, el itinerario se almacena.
- La respuesta informa que la operación fue exitosa.

## HU-05 Consultar itinerarios registrados

**Como** usuario, **quiero** consultar los itinerarios registrados, **para** revisar mis viajes almacenados.

**Requisito:** RF-07. **Prioridad:** alta. **Nivel:** base.

### Criterios de aceptación

- El sistema devuelve todos los itinerarios existentes con su información almacenada.
- Los datos provienen de la base administrada por Itinerary Service.
- Si no existen registros, devuelve una respuesta válida sin error interno.

## HU-06 Consultar detalle de itinerario

**Como** usuario, **quiero** consultar un itinerario específico, **para** revisar sus datos en detalle.

**Requisito:** RF-08. **Prioridad:** alta. **Nivel:** base.

### Criterios de aceptación

- El sistema permite buscar mediante el identificador.
- Un itinerario existente devuelve toda su información.
- Un identificador inexistente produce una respuesta de recurso no encontrado.
- La consulta no modifica datos.

## HU-07 Actualizar itinerario

**Como** usuario, **quiero** modificar un itinerario, **para** actualizar los datos de mi viaje.

**Requisitos:** RF-09, RF-11, RF-12. **Prioridad:** alta. **Nivel:** base.

### Criterios de aceptación

- Se verifica que el itinerario exista.
- Se permite modificar su información.
- Todo aeropuerto modificado se valida nuevamente.
- Una validación fallida impide almacenar cambios.
- Los datos válidos quedan persistidos.

## HU-08 Eliminar itinerario

**Como** usuario, **quiero** eliminar un itinerario que ya no necesito, **para** conservar únicamente los viajes vigentes.

**Requisito:** RF-10. **Prioridad:** alta. **Nivel:** base.

### Criterios de aceptación

- Se verifica que el itinerario exista.
- El registro existente se elimina de la base de datos.
- El itinerario eliminado deja de aparecer en consultas.
- Un identificador inexistente produce una respuesta controlada.

## HU-09 Generar notificación de creación

**Como** usuario, **quiero** recibir una confirmación al crear mi itinerario, **para** saber que fue registrado.

**Requisitos:** RF-14 a RF-17. **Prioridad:** alta. **Nivel:** eventos/Serverless.

### Criterios de aceptación

- La notificación solo se genera después de una creación correcta.
- La creación produce `ItineraryCreatedEvent`.
- El evento se procesa de forma asíncrona.
- Su recepción activa el componente de notificaciones.
- `SendNotificationFunction` simula el envío o registra la acción equivalente.
- El resultado queda almacenado en el historial.
- El procesamiento no bloquea innecesariamente la creación.

## HU-10 Generar reporte de itinerarios

**Como** usuario del sistema, **quiero** generar un reporte de métricas, **para** consultar información consolidada de los viajes.

**Requisito:** RF-18. **Prioridad:** baja. **Nivel:** opcional.

### Criterios de aceptación

- El reporte se ejecuta únicamente bajo demanda.
- La ejecución utiliza `GenerateItineraryReportFunction`.
- La función consolida las métricas requeridas.
- El procesamiento no sobrecarga los servicios principales.

## Regla para el backlog técnico

Docker, Swagger, Redis, Circuit Breaker, RabbitMQ/Kafka, arquitectura hexagonal, DDD, JWT, Jaeger, Kubernetes y otros elementos técnicos deben registrarse como historias técnicas, *enablers* o tareas relacionadas con las épicas. No deben redactarse como necesidades directas del usuario final.
