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
