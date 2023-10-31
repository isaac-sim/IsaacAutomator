variable "prefix" {
  # prefix for all resources and tags created by this module
  type = string
}

variable "ssh_key" {
  default = null
}

variable "region" {
  type = string
}
