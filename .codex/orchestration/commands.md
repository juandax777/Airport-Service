# Comandos del proyecto

Ejecutar solo cuando el usuario pida probar o verificar, o cuando la instrucción de la tarea autorice expresamente esas acciones.

## Preparación local en PowerShell

```powershell
Copy-Item .env.example .env
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e '.[dev]'
```

## Calidad de Python

```powershell
ruff check services
python -m pytest --cov-report=xml
```

`pytest` aplica la cobertura mínima configurada en `pyproject.toml`.

## Docker Compose

```powershell
docker compose config --quiet
docker compose build
docker compose up --build
```

La aplicación web se publica en `http://localhost:8000`; Swagger de Airport Service e Itinerary Service está en los puertos `8001` y `8002`.

No usar `docker compose down --volumes` salvo que el usuario solicite borrar los datos locales. Estos comandos no despliegan Terraform ni infraestructura AWS.
