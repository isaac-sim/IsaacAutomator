resource "alicloud_security_group" "default" {
  name   = "${var.prefix}-sg"
  vpc_id = var.vpc.id
}

# security rule for ssh
resource "alicloud_security_group_rule" "allow_ssh" {
  priority          = 1
  security_group_id = alicloud_security_group.default.id
  type              = "ingress"
  ip_protocol       = "tcp"
  nic_type          = "intranet"
  policy            = "accept"
  port_range        = "22/22"
  cidr_ip           = "0.0.0.0/0"
}

# security rule for novnc
resource "alicloud_security_group_rule" "allow_novnc" {
  priority          = 2
  security_group_id = alicloud_security_group.default.id
  type              = "ingress"
  ip_protocol       = "tcp"
  nic_type          = "intranet"
  policy            = "accept"
  port_range        = "6080/6080"
  cidr_ip           = "0.0.0.0/0"
}

# security rule for ping
resource "alicloud_security_group_rule" "allow_ping" {
  priority          = 3
  security_group_id = alicloud_security_group.default.id
  type              = "ingress"
  ip_protocol       = "icmp"
  nic_type          = "intranet"
  policy            = "accept"
  port_range        = "-1/-1"
  cidr_ip           = "0.0.0.0/0"
}

# security rule for nomachine
resource "alicloud_security_group_rule" "allow_nomachine" {
  priority          = 4
  security_group_id = alicloud_security_group.default.id
  type              = "ingress"
  ip_protocol       = "tcp"
  nic_type          = "intranet"
  policy            = "accept"
  port_range        = "4000/4000"
  cidr_ip           = "0.0.0.0/0"
}

# custom ssh port
resource "alicloud_security_group_rule" "custom_ssh" {
  priority          = 5
  count             = var.ssh_port != 22 ? 1 : 0
  security_group_id = alicloud_security_group.default.id
  type              = "ingress"
  ip_protocol       = "tcp"
  nic_type          = "intranet"
  policy            = "accept"
  port_range        = "${var.ssh_port}/${var.ssh_port}"
  cidr_ip           = "0.0.0.0/0"
}
