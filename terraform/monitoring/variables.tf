variable "function_name" {
  type = string
}

variable "log_group" {
  type = string
}

variable "alarm_actions" {
  type = list(string)
}
