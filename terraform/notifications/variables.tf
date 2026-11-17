variable "name" {
  type = string
}

variable "region" {
  type = string
}

variable "vpc_id" {
  type = string
}

variable "subnet_ids" {
  type = list(string)
}

variable "worker_security_group" {
  type = string
}

variable "broker_security_group" {
  type = string
}

variable "broker_arn" {
  type = string
}

variable "repository_url" {
  type = string
}

variable "repository_name" {
  type = string
}

variable "config" {
  type = object({
    image_digest          = string
    database_secret_arn   = string
    broker_secret_arn     = string
    secrets_kms_key_arns  = optional(set(string), [])
    enabled               = optional(bool, false)
  })
}

variable "other_secrets_client_groups" {
  description = "Clientes que también necesitan el DNS privado de Secrets Manager."
  type        = map(string)
}
