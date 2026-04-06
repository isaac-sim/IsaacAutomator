terraform {
  required_version = ">= 1.3.5"
  backend "local" {}
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.41"
    }
  }
}

provider "aws" {
  region = var.region

  # credentials are provided via AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY,
  # and AWS_SESSION_TOKEN environment variables (from state/.aws/)

  default_tags {
    tags = {
      Deployment = "${var.deployment_name}"
    }
  }
}

module "common" {
  source = "./common"
  prefix = "${var.prefix}.${var.deployment_name}"
  region = var.region
}

module "vpc" {
  source = "./vpc"
  prefix = "${var.prefix}.${var.deployment_name}"
  region = var.region
}

module "isaac_workstation" {
  source            = "./isaac-workstation"
  prefix            = "${var.prefix}.${var.deployment_name}.isaac-workstation"
  count             = var.isaac_workstation_enabled ? 1 : 0
  keypair_id        = module.common.aws_key_pair_id
  instance_type     = var.isaac_workstation_instance_type
  from_image        = var.from_image
  region            = var.region
  ssh_port          = var.ssh_port
  deployment_name   = var.deployment_name
  ingress_cidrs     = var.ingress_cidrs
  prebuilt_ami_name = "${var.prefix}.packer.isaac_image.*"

  iam_instance_profile = null

  vpc = {
    id         = module.vpc.vpc.id
    cidr_block = module.vpc.vpc.cidr_block
  }
}

