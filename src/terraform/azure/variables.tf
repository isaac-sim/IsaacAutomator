variable "prefix" {
  type = string
}

variable "deployment_name" {
  default = "test0"
  type    = string
}

variable "region" {
  default = "westus3"
}

variable "resource_group_name" {
  type = string
}

variable "isaac_workstation_enabled" {
  default = true
}

variable "isaac_workstation_instance_type" {
  type = string
}

variable "from_image" {
  default = false
  type    = bool
}

variable "ssh_port" {
  type = number
}

variable "os_username" {
  type    = string
  default = "ubuntu"
}

