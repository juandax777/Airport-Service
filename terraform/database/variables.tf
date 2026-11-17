variable "name" {
  type = string
}

variable "subnet_ids" {
  type = list(string)
}

variable "instances" {
  type = set(string)
}

variable "security_group_ids" {
  type = map(string)
}

variable "engine_version" {
  type = string
}

variable "instance_class" {
  type = string
}

variable "storage_gib" {
  type = number
}

variable "multi_az" {
  type = bool
}
