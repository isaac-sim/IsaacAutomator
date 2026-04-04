# prefix for created resources and tags
# full name looks like <prefix>.<deployment_name>.<app_name>.<resource_type>
variable "prefix" {
  default = "isa"
  type    = string
}

variable "deployment_name" {
  type = string
}

variable "region" {
  type = string
}

variable "from_image" {
  default = false
  type    = bool
}

variable "ssh_port" {
  type = number
}

variable "isaac_workstation_enabled" {
  type = bool
}

variable "isaac_workstation_instance_type" {
  type = string
}

variable "ingress_cidrs" {
  type = list(string)
}
