variable "prefix" {
  type = string
}

variable "region" {
  type = string
}

variable "vpc_cidr_block" {
  description = "CIDR block for the entire VPC. Will be split into /24 subnet for apps."
  default     = "10.1.0.0/16"
  type        = string
}
