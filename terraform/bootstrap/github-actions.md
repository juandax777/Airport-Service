# GitHub Actions y OIDC

El bootstrap puede crear dos roles por entorno. El rol de publicación escribe imágenes en los cuatro repositorios ECR del proyecto. El rol de planificación consulta AWS, lee el objeto de estado de su entorno y gestiona solo su archivo de bloqueo. El planificador puede leer el estado sensible, por lo que debe ejecutarse desde un entorno protegido. Los roles usan credenciales temporales con audiencia `sts.amazonaws.com` y un sujeto exacto por repositorio y entorno. [OIDC en GitHub Actions](https://docs.github.com/en/actions/how-tos/secure-your-work/security-harden-deployments/oidc-in-aws).

1. Desde una sesión de operador autorizada, habilita `github_actions` en las variables locales del bootstrap. Si la cuenta ya tiene el proveedor OIDC de GitHub, pasa su ARN en `existing_provider_arn`. Para dev usa la clave `dev/terraform.tfstate` y especifica el prefijo ECR de ese entorno. Inicializa el estado remoto con la identidad operativa antes de usar el planificador. El rol de GitHub no puede crear el objeto inicial, migrarlo ni modificarlo.
2. En GitHub, crea `dev-plan` y `dev-publish`. Limita el acceso a la rama `main`, que debe estar protegida, y configura revisores requeridos si el plan de GitHub lo permite. Usa una cuenta y un bootstrap separados para producción, y sus entornos `prod-plan` y `prod-publish`. Copia los ARN del output `github_actions_role_arns` a sus entornos correspondientes.

   | Alcance | Variables y secretos |
   |---|---|
   | Repositorio | Variable `AWS_DEPLOY_ENABLED=true` cuando se habiliten los workflows |
   | Cada entorno | Variables `AWS_REGION` y `AWS_ACCOUNT_ID` |
   | Entorno de plan | Variables `AWS_TERRAFORM_PLAN_ROLE_ARN`, `TF_STATE_BUCKET` y `TF_DEPLOYMENT_CONFIG` |
   | Entorno de plan con Amazon MQ | Secreto `TF_MQ_ADMIN_PASSWORD` |
   | Entorno de publicación | Variables `AWS_ECR_PUBLISH_ROLE_ARN` y `ECR_REPOSITORY_PREFIX` |

3. Define `TF_DEPLOYMENT_CONFIG` como un objeto JSON con las variables de infraestructura del entorno, incluidos los digests y los ARN de secretos cuando se habiliten cargas. El workflow deriva `environment` y `aws_region` del entorno seleccionado. Conserva contraseñas fuera de ese JSON. El backend usa el bucket indicado y la clave del entorno, siempre en el workspace por defecto.
4. Una vez disponibles los repositorios ECR, ejecuta manualmente **Publish images to Amazon ECR** desde `main` y coloca los digests del resumen en la configuración de ECS y Lambda. El workflow **Plan AWS infrastructure** publica el conteo de cambios y libera el bloqueo al terminar. Para investigar fallos o revisar el plan detallado, genera el plan desde la sesión privada del operador con la misma configuración. El runner no publica el plan ni su salida bruta. Las lecturas permitidas en AWS corresponden a los servicios actuales. Si se incorpora un recurso, revisa sus permisos de lectura antes de ampliar el rol. [Permisos del backend S3](https://developer.hashicorp.com/terraform/language/backend/s3#permissions-required).
5. Para desplegar, el operador revisa el plan detallado y aplica el cambio autorizado desde su sesión. Conserva los digests del último despliegue para poder volver a ellos y revisa la compatibilidad de las migraciones antes de revertir.

La publicación se inicia manualmente. La planificación tampoco se ejecuta en pull requests, para mantener el acceso al estado fuera de ramas sin revisar.
