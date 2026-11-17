# Estado remoto de Terraform

El bootstrap administra un bucket por cuenta de infraestructura. Su estado inicial es local. Mantén una copia cifrada en almacenamiento de operadores, con acceso restringido y un único operador a la vez. El bucket tiene versionado, cifrado SSE-S3, TLS obligatorio y bloqueo de acceso público.

En una sesión autorizada, usa credenciales temporales de la cuenta aprobada. Copia el ejemplo de este directorio a `terraform.tfvars` y completa los datos. Desde la raíz del repositorio, inicializa y planifica el bootstrap antes de solicitar autorización para aplicarlo.

```powershell
terraform -chdir=terraform/bootstrap init
terraform -chdir=terraform/bootstrap plan
```

Una vez disponible el bucket, copia `terraform/backend.dev.hcl.example` a `terraform/backend.dev.hcl` y completa su nombre y región. Para una instalación nueva:

```powershell
terraform -chdir=terraform init -backend-config=backend.dev.hcl
```

Si ECR ya está en un estado local, respalda ese estado y usa `init -migrate-state -backend-config=backend.dev.hcl` desde la raíz Terraform que administra ECR. Comprueba que la clave remota no pertenezca a otro estado y revisa las direcciones importadas o migradas antes de aplicar. Coordina la migración para evitar ejecuciones concurrentes.

Usa una clave y credenciales por entorno, por ejemplo `dev/terraform.tfstate` y `prod/terraform.tfstate`. Usa directorios de trabajo separados por entorno para no reutilizar accidentalmente la configuración del backend. En producción se prefiere una cuenta y un bucket propios. El rol de plan requiere s3:ListBucket en el bucket con prefijo acotado y s3:GetObject sobre la clave del estado. Dale GetObject, PutObject y DeleteObject solo para su archivo de bloqueo con sufijo `.tflock`. Agrega PutObject sobre el estado al rol de despliegue. Concede acceso a versiones históricas solo a operadores de recuperación. El bootstrap y el plan de cada entorno tienen ciclos de vida separados. [Permisos del backend S3](https://developer.hashicorp.com/terraform/language/backend/s3#permissions-required).
