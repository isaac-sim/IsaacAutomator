# prefix for created resources and tags
# full name looks like <prefix>.<deployment_name>.<app_name>.<resource_type>
variable "prefix" {
  type = string
}

variable "deployment_name" {
  type = string
}

variable "from_image" {
  default = false
  type    = bool
}

variable "ssh_port" {
  type = number
}

variable "zone" {
  type = string
}

variable "project" {
  type = string
}

variable "isaac_enabled" {
  default = false
  type    = bool
}

variable "isaac_instance_type" {
  type = string
}

variable "isaac_gpu_count" {
  type = number
}

variable "isaac_gpu_type" {
  # "nvidia-tesla-t4" or "nvidia-l4"
  type = string
}

variable "ingress_cidrs" {
  type = list(string)
}

