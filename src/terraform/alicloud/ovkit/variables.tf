variable "prefix" {
  type = string
}

variable "instance_type" {
  type = string
}

variable "ssh_port" {
  type = number
}

variable "vswitch_netnum" {
  description = "The number of the subnet to use for the app vswitch. 1-255."
  type        = number
}

variable "disk_size_gib" {
  type    = number
  default = 256
}

variable "vpc" {
}

variable "resource_group" {
}

variable "key_pair" {
}

