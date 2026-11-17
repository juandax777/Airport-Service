variable "aws_region" {
  type    = string
  default = "us-east-1"
}

variable "project_name" {
  type    = string
  default = "personal-itineraries"
}

variable "environment" {
  type    = string
  default = "dev"
}

variable "network" {
  description = "Configuración de red aprobada por entorno. Null conserva la raíz con ECR únicamente."
  type = object({
    vpc_cidr           = string
    availability_zones = list(string)
    nat_per_az         = optional(bool, false)
  })
  default = null
}

variable "database" {
  description = "Configuración opcional de PostgreSQL. Requiere network."
  type = object({
    engine_version     = optional(string, "16")
    instance_class     = optional(string, "db.t4g.micro")
    storage_gib        = optional(number, 20)
    separate_instances = optional(bool, false)
    multi_az           = optional(bool, false)
  })
  default = null

  validation {
    condition     = var.database == null || var.network != null
    error_message = "Activa network antes de configurar database."
  }
}

variable "messaging" {
  description = "Configuración opcional de Amazon MQ. Requiere network."
  type = object({
    engine_version = optional(string, "4.3")
    instance_type  = optional(string, "mq.m7g.medium")
    cluster        = optional(bool, false)
    admin_username = optional(string, "platform_admin")
  })
  default = null

  validation {
    condition     = var.messaging == null || var.network != null
    error_message = "Activa network antes de configurar messaging."
  }
}

variable "mq_admin_password" {
  description = "Contraseña inicial para crear el broker. Inyectar desde un almacén seguro mediante TF_VAR_mq_admin_password."
  type        = string
  sensitive   = true
  default     = null

  validation {
    condition = var.messaging == null || try(
      length(var.mq_admin_password) >= 12 &&
      length(var.mq_admin_password) <= 250 &&
      !strcontains(var.mq_admin_password, ","),
      false
    )
    error_message = "La contraseña inicial de MQ debe tener 12 a 250 caracteres y excluir comas."
  }
}


variable "compute" {
  description = "Configuración de ECS y del ALB por entorno. Requiere red, PostgreSQL y RabbitMQ."
  type = object({
    image_digests = object({
      airport   = string
      itinerary = string
      web       = string
    })
    hostname             = string
    certificate_arn      = string
    hosted_zone_id       = optional(string)
    itinerary_db_secret  = string
    rabbitmq_url_secret  = string
    secrets_kms_key_arns = optional(set(string), [])
    desired_count        = optional(number, 1)
    log_retention_days   = optional(number, 14)
  })
  default = null

  validation {
    condition     = var.compute == null || (var.network != null && var.database != null && var.messaging != null)
    error_message = "Activa network, database y messaging antes de configurar compute."
  }

  validation {
    condition = var.compute == null || try(alltrue([
      for digest in values(var.compute.image_digests) : can(regex("^sha256:[0-9a-f]{64}$", digest))
    ]), false)
    error_message = "Cada imagen debe identificarse mediante su digest sha256 de ECR."
  }

  validation {
    condition = var.compute == null || try(
      var.compute.desired_count >= 0 && floor(var.compute.desired_count) == var.compute.desired_count,
      false
    )
    error_message = "desired_count debe ser un entero no negativo."
  }
}

variable "notification_worker" {
  description = "Lambda para la cola notifications. Requiere red, PostgreSQL y RabbitMQ."
  type = object({
    image_digest         = string
    database_secret_arn  = string
    broker_secret_arn    = string
    secrets_kms_key_arns = optional(set(string), [])
    enabled              = optional(bool, false)
    alarm_actions        = optional(list(string), [])
  })
  default = null

  validation {
    condition     = var.notification_worker == null || (var.network != null && var.database != null && var.messaging != null)
    error_message = "Activa network, database y messaging antes de configurar notification_worker."
  }

  validation {
    condition     = var.notification_worker == null || can(regex("^sha256:[0-9a-f]{64}$", var.notification_worker.image_digest))
    error_message = "Indica el digest sha256 de la imagen Lambda."
  }
}
