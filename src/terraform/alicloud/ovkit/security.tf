resource "alicloud_security_group" "default" {
  name   = "${var.prefix}-sg"
  vpc_id = var.vpc.id
}
