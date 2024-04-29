terraform {
  required_version = ">= 1.3.5"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.41"
    }
  }
}

provider "aws" {
  region = var.region

  access_key = var.aws_access_key_id
  secret_key = var.aws_secret_access_key

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

module "isaac" {
  source            = "./isaac"
  prefix            = "${var.prefix}.${var.deployment_name}.isaac"
  count             = var.isaac_enabled ? 1 : 0
  keypair_id        = module.common.aws_key_pair_id
  instance_type     = var.isaac_instance_type
  from_image        = var.from_image
  region            = var.region
  ssh_port          = var.ssh_port
  deployment_name   = var.deployment_name
  prebuilt_ami_name = "${var.prefix}.packer.isaac_image.*"

  iam_instance_profile = null

  vpc = {
    id         = module.vpc.vpc.id
    cidr_block = module.vpc.vpc.cidr_block
  }
}

module "metropolis-qs" {
  source          = "./mqs"
  prefix          = "${var.prefix}.${var.deployment_name}.mqs"
  count           = var.mqs_enabled ? 1 : 0
  keypair_id      = module.common.aws_key_pair_id
  instance_type   = var.mqs_instance_type
  from_image      = var.from_image
  region          = var.region
  ssh_port        = var.ssh_port
  deployment_name = var.deployment_name

  iam_instance_profile = null

  vpc = {
    id         = module.vpc.vpc.id
    cidr_block = module.vpc.vpc.cidr_block
  }
}



module "ovami" {
  source          = "./ovami"
  prefix          = "${var.prefix}.${var.deployment_name}.ovami"
  count           = var.ovami_enabled ? 1 : 0
  keypair_id      = module.common.aws_key_pair_id
  ssh_port        = var.ssh_port
  deployment_name = var.deployment_name

  vpc = {
    id         = module.vpc.vpc.id
    cidr_block = module.vpc.vpc.cidr_block
  }
}
