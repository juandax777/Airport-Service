variable "name" {
  type = string
}

variable "vpc_cidr" {
  type = string

  validation {
    condition     = can(cidrnetmask(var.vpc_cidr)) && can(regex("/(1[6-9]|2[0-3])$", var.vpc_cidr))
    error_message = "Usa un CIDR IPv4 de /16 a /23 para reservar subredes de al menos /27."
  }
}

variable "availability_zones" {
  description = "Dos a tres zonas distintas. Conserva el orden para preservar los CIDR asignados."
  type        = list(string)

  validation {
    condition = (
      length(var.availability_zones) >= 2 &&
      length(var.availability_zones) <= 3 &&
      length(distinct(var.availability_zones)) == length(var.availability_zones)
    )
    error_message = "Indica dos o tres zonas de disponibilidad distintas."
  }
}

variable "nat_per_az" {
  description = "Usa un NAT por zona. En false, las subredes de aplicación comparten el NAT de la primera zona."
  type        = bool
}
