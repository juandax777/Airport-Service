# Desarrollo local

## Inicio

1. Instalar Docker Desktop y Docker Compose.
2. Copiar `.env.example` como `.env` y cambiar las contraseñas locales.
3. Ejecutar `docker compose up --build`.
4. Aplicación web: `http://localhost:8000`.
5. Airport Service: `http://localhost:8001/docs`.
6. Itinerary Service: `http://localhost:8002/docs`.
7. RabbitMQ: `http://localhost:15672` con las credenciales definidas en `.env`.

## Calidad

- `pip install -e '.[dev]'`
- `pytest`
- `ruff check services`
- `docker compose build`

No almacenar credenciales, URLs productivas ni archivos `.tfstate` en Git.
