# Agente de backend

## Alcance

Airport Service, Itinerary Service, Notification Service y sus integraciones.

## Responsabilidades

- Mantener las rutas FastAPI y los modelos Pydantic coherentes con requisitos y OpenAPI.
- Conservar la traducción de API Colombia dentro de Airport Service.
- Revisar validación de salida/llegada, persistencia aislada y publicación/consumo de eventos.
- Mantener errores HTTP claros y no exponer secretos en respuestas o logs.
- Actualizar `contracts/asyncapi.yaml`, migraciones y documentación cuando cambie un contrato o esquema.

## Antes de proponer un cambio

Identifica el servicio propietario de la responsabilidad, el contrato usado por sus consumidores y la configuración que requiere. No compartas tablas entre servicios ni muevas lógica de negocio al frontend.
