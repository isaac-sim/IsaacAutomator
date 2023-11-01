

variable "region" {
  description = "Region we're creating resources in."
  type        = string
}

variable "vpc_cidr_block" {
  description = "CIDR block for the entire VPC. Will be split into /24 subnets."
  default     = "10.1.0.0/16"
  type        = string
}

variable "prefix" {
  description = "Prefix for all resources this module creates."
  type        = string
}
