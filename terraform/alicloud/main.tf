terraform {
  required_version = ">= 1.3.5"
}

provider "alicloud" {
  access_key = var.alicloud_access_key
  secret_key = var.alicloud_secret_key
  region     = var.region
}

module "isaac" {
  source          = "./ovkit"
  count           = var.isaac_enabled ? 1 : 0
  isaac_enabled   = var.isaac_enabled
  prefix          = "${var.prefix}.${var.deployment_name}.isaac"
  deployment_name = var.deployment_name
  instance_type   = var.isaac_instance_type
  ssh_port        = var.ssh_port
}
