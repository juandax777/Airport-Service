# Restricciones de trabajo

## Integridad del repositorio

- No leer, imprimir ni copiar secretos de `.env`; usa `.env.example` para conocer nombres de variables.
- No versionar `.env`, bases locales, reportes generados, `.venv`, ni archivos `terraform.tfstate`, planes o variables reales.
- No ejecutar `terraform apply`, publicar imágenes, desplegar, fusionar PR ni modificar servicios externos sin una solicitud explícita.
- No cambiar contratos HTTP o `ItineraryCreatedEvent` sin revisar consumidores, AsyncAPI y documentación afectada.

## Diseño

- Mantén límites claros entre web, Airport Service, Itinerary Service y Notification Service.
- Conserva la base de datos propia por servicio; no acoples un servicio a las tablas de otro.
- Trata API Colombia como proveedor externo y traduce sus datos en Airport Service.
- Mantén configuración sensible fuera del código y lee configuración mediante variables de entorno.
- Evita agregar dependencias si la biblioteca estándar o el stack existente resuelve el problema.
- Preserva compatibilidad con Python 3.12 y la ejecución local con Docker Compose.

## Cambios y validación

- Sigue el flujo de ramas y revisión de `CONTRIBUTING.md`; no trabajes directamente sobre `main` cuando el entorno proporcione una rama de trabajo.
- No ejecutes pruebas ni agregues pruebas nuevas salvo que el usuario lo pida. Si solicita verificación, empieza por los comandos aplicables en `.codex/orchestration/commands.md`.
- Informa con precisión qué comandos se ejecutaron y cuáles no.
- No actualices simultáneamente manifiestos de dependencias distintos por suposición; explica si una dependencia está declarada en `pyproject.toml` y en `requirements.txt`.
