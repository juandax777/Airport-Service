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
