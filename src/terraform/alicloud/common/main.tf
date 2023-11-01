# ssh key
resource "tls_private_key" "ssh_key" {
  algorithm = "RSA"
  rsa_bits  = 4096
}

# resource group
resource "alicloud_resource_manager_resource_group" "default" {
  resource_group_name = "${var.prefix}-rg"
  display_name        = "${var.prefix}-rg"
}

# keypair
resource "alicloud_ecs_key_pair" "default" {
  key_pair_name     = "${var.prefix}-keypair"
  public_key        = tls_private_key.ssh_key.public_key_openssh
  resource_group_id = alicloud_resource_manager_resource_group.default.id
}

# create vpc on alicloud
resource "alicloud_vpc" "default" {
  vpc_name          = "${var.prefix}-vpc"
  cidr_block        = var.vpc_cidr_block
  resource_group_id = alicloud_resource_manager_resource_group.default.id
}
