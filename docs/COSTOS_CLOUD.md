# Estimación de costos de AWS

Esta guía estima el costo mensual de la infraestructura AWS del Sistema de Itinerarios Personales. Los importes son aproximados en USD para `us-east-1`, precios bajo demanda, 730 horas al mes y sin impuestos, créditos ni transferencia significativa. AWS factura los recursos y el tráfico reales, no por cantidad de usuarios registrados. El número de personas sirve como referencia de carga, y el número de tareas, capacidad de base de datos y tráfico determinan el importe.

## Supuestos de arquitectura

La estimación base representa el despliegue de desarrollo documentado en `terraform/`: tres tareas ECS Fargate Linux x86 (Web, Airport e Itinerary), cada una con 0.5 vCPU y 1 GiB; ALB público; un NAT Gateway; tres IPv4 públicas; RabbitMQ Amazon MQ de una instancia `mq.m7g.medium`; RDS PostgreSQL Single-AZ `db.t4g.micro` con 20 GiB gp3; y cuatro endpoints de interfaz, incluidos Lambda, Secrets Manager, STS y el servicio privado usado por la función. Para endpoints en dos zonas se cuentan seis ENI para los tres endpoints de AWS y una ENI para el endpoint privado adicional.

La configuración real puede variar. Contrasta este modelo con las variables del entorno y los recursos visibles en AWS antes de presupuestar o desplegar. Desactivar el disparador de Lambda evita su consumo, pero los endpoints, el broker y otros recursos aprovisionados pueden seguir cobrando.

## Costos mensuales con el entorno encendido

| Servicio o recurso | Base estimada USD/mes | Cómo se cobra |
|---|---:|---|
| ECS Fargate, 3 tareas | 54 | vCPU, memoria, sistema operativo, arquitectura y tiempo de ejecución. Cada tarea adicional del tamaño supuesto agrega unos 18.02 al mes si permanece activa todo el mes. |
| Application Load Balancer | 16–23 | Horas provisionadas, unidades LCU, reglas y tráfico. |
| NAT Gateway | 33 | Horas provisionadas, más datos procesados y transferencia. |
| IPv4 públicas, 3 direcciones | 11 | Horas de cada dirección pública asociada, tanto en uso como inactiva. |
| Amazon MQ RabbitMQ `mq.m7g.medium`, una instancia | 100–102 | Horas de broker y almacenamiento configurado. El broker no tiene pausa; para dejar de pagar cómputo hay que eliminarlo. |
| RDS PostgreSQL `db.t4g.micro`, 20 GiB gp3, Single-AZ | 14 | Horas de instancia y almacenamiento. Al detener RDS, se mantiene el cargo de almacenamiento y respaldos aplicables. |
| Endpoints de interfaz de VPC | 44–51 | Horas por endpoint y zona de disponibilidad, más datos procesados. La cifra depende de las zonas configuradas. |
| ECR, S3, Secrets Manager, CloudWatch, Cloud Map, Route 53 y transferencia | 1–20+ | Almacenamiento, solicitudes, secretos activos, logs, descubrimiento de servicios, consultas DNS y transferencia real. Retención larga de logs o artefactos aumenta el importe. |
| **Total orientativo** | **273–308+** | El tráfico alto, despliegue Multi-AZ, respaldo adicional o mayor capacidad elevan el total. |

El rango representa un entorno disponible continuamente. Es una estimación de arquitectura, no una cotización ni el importe de la factura de una cuenta específica. No suma posibles cargos fiscales, soporte de AWS, IPv4 adicionales, cuotas de API externa ni transferencias entre zonas no contempladas.

## Escenarios de usuarios

Los escenarios suponen usuarios activos al mismo tiempo en horas pico y que ECS escala horizontalmente cuando hace falta. Para hacer comparables los ejemplos, cada tarea mantiene el tamaño de 0.5 vCPU y 1 GiB de la configuración base. Los valores de tráfico son orientativos; solicitudes por usuario, caché, tamaño de respuesta, frecuencia de consultas y duración de la actividad cambian el resultado.

| Escenario de referencia | ECS supuesto | Total aproximado USD/mes | Lectura del escenario |
|---|---:|---:|---|
| Hasta 10 usuarios simultáneos | 1 tarea por servicio, 3 en total | 273–307+ | Carga baja. La mayor parte del costo corresponde a recursos fijos de red, broker, base y endpoints. |
| Hasta 100 usuarios simultáneos | 2 tareas por servicio, 6 en total | 327–362+ | Duplica la capacidad ECS. Revisar conexiones concurrentes, CPU, memoria y latencia de RDS. |
| Hasta 500 usuarios simultáneos | 3 tareas por servicio, 9 en total | 381–416+ | Puede requerir aumentar también la clase de RDS y ajustar RabbitMQ, además de ECS. |
| Hasta 1.000 usuarios simultáneos | 6 tareas por servicio, 18 en total | 543–578+ | Es un escenario de dimensionamiento inicial, no una garantía de capacidad. Requiere prueba de carga y revisar límites del broker, base, red y dependencias externas. |

El cálculo de escenarios incrementa únicamente ECS en aproximadamente USD 18.02 por tarea adicional al mes. No presupone que la base o el broker soporten esas concurrencias. Un usuario registrado que usa la aplicación ocasionalmente no equivale a un usuario simultáneo. En cada entorno, define concurrencia pico, solicitudes por minuto, itinerarios creados y datos transferidos para afinar el cálculo.

## Qué recursos cobran aunque no haya usuarios

- **Cargos mayormente fijos mientras están provisionados:** NAT Gateway, ALB, Amazon MQ, endpoints de interfaz, tareas Fargate con Desired count mayor que cero e IPv4 públicas.
- **Cargos parcialmente variables:** RDS combina cómputo y almacenamiento; Fargate cobra por las tareas y su duración; ALB, NAT y endpoints agregan cargos por tráfico o unidades procesadas.
- **Cargos de almacenamiento y operaciones:** imágenes de ECR, objetos de S3 y estado de Terraform, respaldos de RDS, secretos y logs de CloudWatch.
- **Lambda:** invocaciones y duración, más almacenamiento y logs relacionados. Sin invocaciones el costo suele ser bajo, pero endpoints de VPC asociados pueden cobrar por hora.
- **Servicios externos:** API Colombia puede tener límites o condiciones de uso propios que no aparecen en la factura de AWS.

Poner Desired count de ECS en cero detiene el cómputo de las tareas cuando llegan a cero. No detiene ALB, NAT, RabbitMQ, endpoints, almacenamiento ni RDS. RDS detenido se inicia automáticamente después de siete días. Amazon MQ no ofrece pausa para el broker.

## Modelo de costo al apagar el entorno

Para una demo ocasional, mantener toda la arquitectura encendida cada hora del mes cuesta mucho más que sus periodos de uso. Si se conserva la base, RDS se puede detener temporalmente, manteniendo su almacenamiento. Al terminar un broker Amazon MQ, eliminarlo evita el cargo por hora, pero interrumpe RabbitMQ y requiere crear/configurar otro para reanudar el procesamiento. Eliminar NAT, ALB y endpoints reduce cargos fijos de red, aunque requiere recrearlos para volver a exponer y conectar la aplicación.

Antes de borrar infraestructura administrada con Terraform, actualiza el código y el estado siguiendo el procedimiento del entorno. Borrar recursos desde la consola sin reconciliar Terraform puede producir diferencias y que un `apply` futuro los cree de nuevo. Conserva el bucket y el estado de Terraform mientras todavía necesites administrar recursos existentes.

## Método para ajustar el presupuesto

1. Define región, horas activas al mes, usuarios simultáneos máximos, solicitudes por minuto, datos transferidos, retención de logs y disponibilidad requerida.
2. Ajusta cantidad y tamaño de tareas, clase y almacenamiento de RDS, tipo y almacenamiento de Amazon MQ, cantidad de zonas, NAT, ALB y endpoints.
3. Usa [AWS Pricing Calculator](https://calculator.aws/) para cotizar los recursos y la región reales antes del despliegue.
4. Después de desplegar, compara mensualmente AWS Cost Explorer por servicio y región. Activa un presupuesto de AWS con alertas para detectar desvíos.

## Referencias de tarifas

Precios públicos consultados para la elaboración del modelo. Las tarifas pueden cambiar y variar por región y configuración.

- [AWS Fargate](https://aws.amazon.com/fargate/pricing/)
- [Application Load Balancer](https://aws.amazon.com/elasticloadbalancing/pricing/)
- [Amazon VPC, NAT Gateway e IPv4 pública](https://aws.amazon.com/vpc/pricing/)
- [AWS PrivateLink y endpoints](https://aws.amazon.com/privatelink/pricing/)
- [Amazon MQ](https://aws.amazon.com/amazon-mq/pricing/) y [clases RabbitMQ](https://docs.aws.amazon.com/amazon-mq/latest/developer-guide/rmq-broker-instance-types.html)
- [RDS for PostgreSQL](https://aws.amazon.com/rds/postgresql/pricing/)
- [AWS Pricing Calculator](https://calculator.aws/)
