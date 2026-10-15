# Flujo de trabajo

## 1. Entender

Lee el objetivo del usuario, el `AGENTS.md` aplicable, el requisito/historia y los archivos del servicio afectado. Comprueba el estado del repositorio antes de editar.

## 2. Trazar

Identifica el servicio propietario, consumidores, contratos, manifiestos de dependencias, configuración, workflow y documentación afectados. En cambios transversales, registra el orden de dependencias.

## 3. Diseñar

Elige la solución más pequeña que cumpla los criterios y conserve los límites de arquitectura. Si hay una contradicción de alcance, señala la decisión pendiente antes de asumirla.

## 4. Implementar

Haz cambios enfocados y evita mezclar limpieza no relacionada. Mantén consistencia entre `pyproject.toml` y los `requirements.txt` usados por Docker cuando el cambio afecte dependencias.

## 5. Revisar

Inspecciona el diff, archivos generados y posibles secretos. Ejecuta verificaciones solo cuando el usuario las haya solicitado. Para cambios externos o destructivos, detente antes de la acción y sigue las reglas de autorización de la sesión.

## 6. Entregar

Resume qué cambió, por qué, qué verificaciones se realizaron y qué queda por confirmar. Incluye archivos relevantes y riesgos materiales.
