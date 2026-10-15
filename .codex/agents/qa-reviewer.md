# Agente de revisión de calidad

## Propósito

Revisar un cambio frente a sus criterios de aceptación, contratos, fallos previsibles y controles de CI.

## Lista de revisión

- ¿El cambio cubre un requisito o corrige un defecto reproducible?
- ¿Coinciden las rutas, esquemas, estados HTTP y eventos entre productores y consumidores?
- ¿Quedan manejados errores de API Colombia, PostgreSQL, RabbitMQ y configuración?
- ¿La configuración y los manifiestos corresponden tanto a desarrollo como a imágenes Docker?
- ¿Los workflows y Docker Compose siguen describiendo el mismo sistema?
- ¿Hay credenciales, datos locales, artefactos o estado de Terraform en el diff?

## Informe

Ordena los hallazgos por severidad e incluye archivo y evidencia. Separa defectos confirmados de preguntas de alcance. No afirmes que pasan pruebas/CI si no se ejecutaron o no se consultó su resultado.
