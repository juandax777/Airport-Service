# Manual de ejecución local

Este manual ejecuta la primera versión del backend: Airport Service, Itinerary Service, RabbitMQ y dos bases PostgreSQL aisladas. No requiere una cuenta AWS ni despliega recursos en la nube.

## 1. Requisitos previos

Instala y verifica los siguientes programas:

- Docker Desktop para Windows, iniciado y usando contenedores Linux.
- Docker Compose v2, incluido en Docker Desktop.
- Git, si deseas trabajar con ramas y commits.
- Python 3.12 solo si ejecutarás pruebas fuera de Docker.

Abre PowerShell en la carpeta raíz del proyecto y ejecuta:

```powershell
docker --version
docker compose version
```

Ambos comandos deben devolver una versión. Si Docker Desktop no está abierto, inícialo y espera a que indique que el motor está listo.

Prepara la configuración local. El archivo `.env` está ignorado por Git:

```powershell
Copy-Item .env.example .env
```

Puedes mantener los valores de desarrollo o cambiar las contraseñas antes de iniciar los contenedores.

## 2. Iniciar todos los componentes

Desde la raíz del proyecto ejecuta:

```powershell
docker compose up --build
```

La primera ejecución descarga imágenes y dependencias, por lo que tarda más. Mantén esa consola abierta para ver los logs.

Para ejecutar en segundo plano:

```powershell
docker compose up --build -d
```

Comprueba el estado:

```powershell
docker compose ps
```

Los servicios esperados son `web-app`, `airport-service`, `itinerary-service`, `notification-service`, `itinerary-db`, `notification-db` y `rabbitmq`.

## 3. Direcciones locales

| Componente | Dirección | Uso |
|---|---|---|
| Aplicación web | http://localhost:8000 | Mapa y gestión visual de itinerarios. |
| Airport Service | http://localhost:8001/docs | Swagger y consulta de aeropuertos. |
| Itinerary Service | http://localhost:8002/docs | Swagger y CRUD de itinerarios. |
| RabbitMQ Management | http://localhost:15672 | Revisar colas, intercambios y mensajes. |
| RabbitMQ Management | Variables `RABBITMQ_USER` y `RABBITMQ_PASSWORD` de `.env` | Credenciales válidas solo para desarrollo local. |

## 4. Verificar que los servicios estén saludables

En otra consola PowerShell:

```powershell
Invoke-RestMethod http://localhost:8001/health/live
Invoke-RestMethod http://localhost:8002/health/live
```

Ambas respuestas deben incluir `status: ok`.

Puedes abrir Swagger desde el navegador para explorar los contratos HTTP:

- `http://localhost:8001/docs`
- `http://localhost:8002/docs`

## 5. Probar el flujo principal

### Consultar un aeropuerto

Primero consulta un aeropuerto válido mediante Swagger o con PowerShell. El identificador disponible depende de API Colombia:

```powershell
Invoke-RestMethod http://localhost:8001/api/v1/airports
Invoke-RestMethod http://localhost:8001/api/v1/airports/1
```

Si el ID `1` no existe, toma un identificador de la respuesta de la lista.

### Crear un itinerario

Reemplaza los IDs por dos aeropuertos existentes. El comando siguiente utiliza `1` y `2` como ejemplo:

```powershell
$payload = @{
  user_name = 'Juan David'
  departure_airport_id = '1'
  arrival_airport_id = '2'
  travel_date = '2026-12-15'
  duration_minutes = 90
} | ConvertTo-Json

Invoke-RestMethod -Method Post `
  -Uri http://localhost:8002/api/v1/itineraries `
  -ContentType 'application/json' `
  -Body $payload
```

La respuesta debe devolver el itinerario con su `id`. La creación realiza estas acciones:

1. Itinerary Service valida salida y llegada con Airport Service.
2. Guarda el itinerario en `itinerary-db`.
3. Publica `ItineraryCreatedEvent` en RabbitMQ.
4. Notification Service consume el evento y registra una notificación simulada en `notification-db`.

Para consultar los itinerarios:

```powershell
Invoke-RestMethod http://localhost:8002/api/v1/itineraries
```

## 6. Consultar logs y RabbitMQ

Ver logs de todos los componentes:

```powershell
docker compose logs -f
```

Ver logs de un servicio específico:

```powershell
docker compose logs -f itinerary-service
docker compose logs -f notification-service
```

En RabbitMQ Management revisa:

- El exchange `itineraries`.
- La cola `notifications`.
- Los mensajes pendientes o no reconocidos.

## 7. Detener o reiniciar

Detener contenedores sin borrar información:

```powershell
docker compose down
```

Detener y eliminar datos locales de PostgreSQL y RabbitMQ:

```powershell
docker compose down --volumes
```

Usa el segundo comando solo si deseas empezar desde cero; elimina los itinerarios y el historial de notificaciones locales.

Recrear un único componente tras cambios:

```powershell
docker compose up --build airport-service
```

## 8. Ejecutar pruebas y calidad

Para ejecutar pruebas fuera de Docker necesitas instalar dependencias de desarrollo:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e '.[dev]'
pytest
ruff check services
```

La integración continua en GitHub ejecuta pytest, Ruff, build de imágenes y Trivy. OWASP ZAP se ejecuta manualmente o por programación desde el workflow de seguridad.

## 9. Problemas frecuentes

### El puerto ya está ocupado

Detén el proceso que usa el puerto o cambia la parte izquierda del mapeo de puertos en `docker-compose.yml`. Por ejemplo, para Airport Service: `8003:8000`.

### Airport Service responde 503

API Colombia no está disponible o no puede alcanzarse desde el contenedor. Revisa tu conexión y los logs:

```powershell
docker compose logs airport-service
```

### Itinerary Service responde 422

Uno de los aeropuertos no existe, ambos IDs son iguales, o la duración no es positiva. Consulta primero Airport Service y usa dos IDs válidos.

### Itinerary Service responde 503 al crear

RabbitMQ o Airport Service no están disponibles. Ejecuta `docker compose ps` y revisa los logs de ambos servicios.

### Docker muestra errores de permisos de configuración

Abre Docker Desktop con el usuario propietario del proyecto, verifica que esté iniciado y vuelve a ejecutar el comando desde una consola normal de PowerShell. No borres archivos de Docker manualmente sin confirmar primero que no contengan credenciales o configuraciones necesarias.

## 10. Nota sobre AWS

La carpeta `terraform/` prepara la futura infraestructura AWS, pero este manual no ejecuta `terraform apply`. No se crean recursos ni se generan costos en AWS al ejecutar Docker Compose localmente.
