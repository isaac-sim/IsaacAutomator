variable "prefix" {
  type = string
}

variable "instance_type" {
  type = string
}

variable "ssh_port" {
  type = number
}

variable "isaac_enabled" {
  type = bool
}

variable "vswitch_netnum" {
  description = "The number of the subnet to use for the app vswitch. 1-255."
  type        = number
}

variable "system_disk_category" {
  description = "Category of the system disk: ephemeral_ssd, cloud_efficiency, cloud_ssd, cloud_essd, cloud, cloud_auto."
  type        = string
  default     = "cloud_ssd"
}

variable "system_disk_size" {
  description = "Size of the system disk in GiB."
  type        = number
  default     = 256
}

variable "vpc" {
}

variable "resource_group" {
}

variable "key_pair" {
}

