terraform {
  required_version = ">= 1.3.5"
}

provider "alicloud" {
  access_key = var.aliyun_access_key
  secret_key = var.aliyun_secret_key
  region     = var.region
}

module "common" {
  source = "./common"
  prefix = "${var.prefix}-${var.deployment_name}-common"
  region = var.region
}

module "isaac" {
  count = var.isaac_enabled ? 1 : 0

  source         = "./ovkit"
  prefix         = "${var.prefix}-${var.deployment_name}-isaac"
  vswitch_netnum = 1

  ssh_port       = var.ssh_port
  isaac_enabled  = var.isaac_enabled
  vpc            = module.common.vpc
  key_pair       = module.common.key_pair
  instance_type  = var.isaac_instance_type
  resource_group = module.common.resource_group
}
