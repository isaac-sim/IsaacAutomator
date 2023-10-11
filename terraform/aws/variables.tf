# prefix for created resources and tags
# full name looks like <prefix>.<deployment_name>.<app_name>.<resource_type>
variable "prefix" {
  default = "auto-isaac"
  type    = string
}

variable "deployment_name" {
  type = string
}

variable "region" {
  type = string
}

variable "ovami_enabled" {
  type = bool
}

variable "from_image" {
  default = false
  type    = bool
}

variable "aws_access_key_id" {
  type = string
}

variable "aws_secret_access_key" {
  type = string
}

variable "ssh_port" {
  type = number
}

variable "isaac_enabled" {
  type = bool
}

variable "isaac_instance_type" {
  type = string
}
