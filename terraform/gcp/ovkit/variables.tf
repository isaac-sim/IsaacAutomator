variable "prefix" {
  type = string
}

variable "deployment_name" {
  type = string
}

variable "public_key_openssh" {
  type = string
}

variable "instance_type" {
  type = string
}

variable "gpu_count" {
  type = number
}

variable "gpu_type" {
  type = string
}

variable "ssh_port" {
  type = number
}

variable "isaac_enabled" {
  type    = bool
  default = false
}
