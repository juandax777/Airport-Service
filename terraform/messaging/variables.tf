variable "name" {
  type = string
}

variable "engine_version" {
  type = string
}

variable "instance_type" {
  type = string
}

variable "cluster" {
  type = bool
}

variable "subnet_ids" {
  type = list(string)
}

variable "security_group_id" {
  type = string
}

variable "admin_username" {
  type = string
}

variable "admin_password" {
  type      = string
  sensitive = true
}
