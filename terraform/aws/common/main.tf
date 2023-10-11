# ssh key
resource "tls_private_key" "ssh_key" {
  algorithm = "RSA"
  rsa_bits  = 4096
}

# keypair
resource "aws_key_pair" "keypair" {
  key_name   = "${var.prefix}.keypair"
  public_key = tls_private_key.ssh_key.public_key_openssh

  tags = {
    Name = "${var.prefix}.keypair"
  }
}
