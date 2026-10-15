# Agente de interfaz web

## Alcance

`services/web_app`, sus plantillas Jinja, CSS y JavaScript.

## Responsabilidades

- Mantener la interfaz servida por la aplicación web existente, sin introducir un framework frontend sin justificación.
- Consumir Airport Service e Itinerary Service a través de sus APIs internas.
- Mantener la representación del mapa compatible con los datos geográficos que entrega Airport Service y Plotly JS.
- Conservar accesibilidad, mensajes de validación claros y funcionamiento con los endpoints actuales.
- Evitar exponer secretos o direcciones internas de servicios al navegador cuando no sean necesarias.

Antes de cambiar la interfaz, revisa las rutas de `services/web_app/app/main.py` y los criterios de aceptación de la historia afectada.
