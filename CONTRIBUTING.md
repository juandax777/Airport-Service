# Guía de contribución

## Flujo de ramas

- `main` contiene únicamente código revisado y listo para demostración.
- Cada cambio se desarrolla en una rama corta: `feature/<descripcion>`, `fix/<descripcion>`, `docs/<descripcion>` o `chore/<descripcion>`.
- No se realizan commits directos en `main`.
- Todo cambio entra mediante Pull Request y requiere al menos una aprobación de otro integrante.
- Los contratos HTTP, OpenAPI, AsyncAPI y `ItineraryCreatedEvent` requieren revisión de los tres integrantes.

## Preparación local

```powershell
Copy-Item .env.example .env
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e '.[dev]'
```

Consulta [`docs/MANUAL_EJECUCION.md`](docs/MANUAL_EJECUCION.md) para ejecutar todo el sistema.

## Antes de abrir un Pull Request

```powershell
ruff check services
python -m pytest --cov-report=xml
docker compose config --quiet
docker compose build
```

El Pull Request debe explicar el cambio, cómo se probó y qué requisito o historia de usuario cubre. No incluyas archivos `.env`, bases locales, reportes, credenciales, estados de Terraform ni contenido de `.venv`.

## Convención de commits

Se recomienda Conventional Commits:

- `feat(airport): agrega búsqueda por ciudad`
- `fix(itinerary): valida aeropuertos diferentes`
- `test(notification): cubre eventos duplicados`
- `docs: actualiza ejecución local`
- `chore(ci): actualiza análisis de seguridad`

## Definition of Done

- Cumple sus criterios de aceptación.
- Incluye o actualiza pruebas automatizadas.
- Mantiene cobertura mínima de 70 %.
- Pasa Ruff, pytest y el build Docker.
- Actualiza contratos y documentación cuando corresponda.
- No introduce secretos ni artefactos locales.
