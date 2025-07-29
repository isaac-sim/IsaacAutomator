variable "prefix" {
  type = string
}

variable "keypair_id" {
  type = string
}

variable "instance_type" {
  default = "g5.4xlarge"
  type    = string
}

variable "region" {
  default = "us-east-1"
  type    = string
}

variable "vpc" {
  type = object({
    id         = string,
    cidr_block = string,
  })
}

variable "base_ami_name" {
  default = "ubuntu/images/hvm-ssd/ubuntu-*-20.04-amd64-server-*"
}

variable "ssh_port" {
  default = 22
  type    = number
}

variable "deployment_name" {
  type = string
}

variable "ingress_cidrs" {
  type = list(string)
}
