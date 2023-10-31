# ssh key

resource "tls_private_key" "ssh_key" {
  algorithm = "RSA"
  rsa_bits  = 4096
}

# keypair
# TODO: specify resource_group_id (@see https://registry.terraform.io/providers/aliyun/alicloud/latest/docs/resources/key_pair#resource_group_id)
resource "alicloud_key_pair" "default" {
  key_pair_name = "${var.prefix}.${var.deployment_name}.keypair"
  public_key    = tls_private_key.ssh_key.public_key_openssh

  tags = {
    Name = "${var.prefix}.${var.deployment_name}.keypair"
  }
}
