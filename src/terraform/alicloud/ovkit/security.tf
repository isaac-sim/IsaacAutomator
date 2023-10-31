resource "alicloud_security_group" "default" {
  name   = "${var.prefix}-sg"
  vpc_id = var.vpc.id
}

# security rule for ssh
resource "alicloud_security_group_rule" "allow_ssh" {
  type              = "ingress"
  ip_protocol       = "tcp"
  nic_type          = "intranet"
  policy            = "accept"
  port_range        = "22/22"
  priority          = 1
  security_group_id = alicloud_security_group.default.id
  cidr_ip           = "0.0.0.0/0"
}

# security rule for novnc
resource "alicloud_security_group_rule" "allow_novnc" {
  type              = "ingress"
  ip_protocol       = "tcp"
  nic_type          = "intranet"
  policy            = "accept"
  port_range        = "6080/6080"
  priority          = 2
  security_group_id = alicloud_security_group.default.id
  cidr_ip           = "0.0.0.0/0"
}
