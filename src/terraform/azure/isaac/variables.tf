variable "prefix" {
  default = null
}

variable "rg" {
  default = null
}

variable "subnet" {
  default = null
}

variable "ssh_key" {
  default = null
}

variable "vm_type" {
  type = string
}

variable "from_image" {
  default = false
  type    = bool
}

variable "ssh_port" {
  type = number
}
