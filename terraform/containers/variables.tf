variable "name" {
  type = string
}

variable "region" {
  type = string
}

variable "vpc_id" {
  type = string
}

variable "public_subnet_ids" {
  type = list(string)
}

variable "private_subnet_ids" {
  type = list(string)
}

variable "itinerary_data_group_id" {
  type = string
}

variable "repositories" {
  type = map(object({
    url = string
    arn = string
  }))
}

variable "config" {
  type = object({
    image_digests = object({
      airport   = string
      itinerary = string
      web       = string
    })
    hostname               = optional(string)
    certificate_arn        = optional(string)
    hosted_zone_id         = optional(string)
    allowed_web_cidrs      = set(string)
    itinerary_db_secret   = string
    rabbitmq_url_secret    = string
    secrets_kms_key_arns   = optional(set(string), [])
    desired_count          = optional(number, 1)
    log_retention_days     = optional(number, 14)
  })
}
