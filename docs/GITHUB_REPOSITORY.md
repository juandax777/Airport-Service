# Preparación y publicación en GitHub

## Estructura del repositorio

```text
.
├── .github/                 Workflows y plantillas de colaboración
├── contracts/               Contratos AsyncAPI y futuros contratos compartidos
├── docs/                    Requisitos, historias y manuales
├── services/
│   ├── airport_service/
│   ├── itinerary_service/
│   ├── notification_service/
│   └── web_app/
├── terraform/               Infraestructura AWS preparada, no aplicada
├── .env.example             Variables locales sin secretos
├── docker-compose.yml       Entorno completo de desarrollo
└── pyproject.toml           Dependencias y herramientas Python
```

Las bases SQLite, entornos virtuales, cachés, reportes, `.env` y estados de Terraform son exclusivamente locales y están excluidos por `.gitignore`.

## Crear el repositorio remoto

1. Crea en GitHub un repositorio vacío, sin README, licencia ni `.gitignore generados por GitHub.
2. Desde la raíz local revisa lo que se publicará:

```powershell
git status --short
git status --ignored --short
git diff --check
```

3. Crea el primer commit:

```powershell
git add .
git commit -m "chore: initialize personal itineraries platform"
```

4. Conecta el repositorio. Reemplaza `<organizacion>` y `<repositorio>`:

```powershell
git remote add origin https://github.com/<organizacion>/<repositorio>.git
git push -u origin main
```

No ejecutes `git add -f` sobre archivos ignorados.

## Protección recomendada para `main`

En GitHub, abre **Settings → Branches → Add branch protection rule** y configura:

- patrón `main`;
- Pull Request obligatorio;
- al menos una aprobación;
- aprobación nueva después de cambios adicionales;
- conversaciones resueltas antes de fusionar;
- checks obligatorios del workflow `CI`;
- impedir force-push y eliminación de la rama.

Para un equipo de tres, usa una revisión cruzada: el propietario del servicio desarrolla y otro integrante aprueba. Los contratos compartidos requieren aprobación de todo el equipo.

## Variables y secretos de GitHub

La ejecución local usa `.env`. GitHub Actions no debe recibir ese archivo. Para la publicación opcional en AWS configura:

### SonarQube opcional

El análisis de SonarQube es opcional para que los PR y el CI normal funcionen sin una cuenta configurada. Para habilitarlo en **Settings → Secrets and variables → Actions**:

- Variable `SONARQUBE_ENABLED`: `true`.
- Variable `SONAR_HOST_URL`: URL accesible desde GitHub Actions; para SonarQube Cloud usa `https://sonarcloud.io`.
- Secreto `SONAR_TOKEN`: token del proyecto con permiso para analizarlo.

Si la variable de activación no es `true`, o falta la URL o el token, el paso de análisis se omite. El proyecto de SonarQube debe existir y usar la clave declarada en `sonar-project.properties`. Para SonarQube Cloud, configura también `sonar.organization` en ese archivo con la clave de la organización.

### Variables del repositorio

- `AWS_DEPLOY_ENABLED`: `true` únicamente cuando se habilite la publicación.
- `AWS_REGION`: por ejemplo, `us-east-1`.
- `ECR_REPOSITORY_PREFIX`: prefijo creado por Terraform, por ejemplo `personal-itineraries-dev`.

### Secretos del repositorio

- `AWS_GITHUB_ACTIONS_ROLE_ARN`: ARN del rol asumible mediante GitHub OIDC.

No guardes access keys permanentes de AWS. La configuración prevista utiliza OIDC y permisos temporales.

## Archivos que deben permanecer fuera de Git

- `.env` y cualquier variante local o productiva.
- `.venv/`, `__pycache__/`, cobertura y cachés de herramientas.
- `*.db`, `*.sqlite` y volúmenes locales.
- `.terraform/`, `*.tfstate`, planes y archivos de variables reales.
- reportes de ZAP, SonarQube y Trivy.
- configuraciones personales de IDE.

Antes de cada publicación ejecuta `git status --ignored --short` y confirma que estos elementos figuren como ignorados.

## Licencia

No se agregó una licencia automáticamente porque el equipo debe decidir las condiciones de uso. Si el proyecto será público, acuerden una licencia antes de publicarlo; sin licencia, terceros no reciben permiso general para reutilizar el código.
