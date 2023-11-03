# find zones where instance is available

data "alicloud_zones" "instance_availability" {
  available_instance_type = var.instance_type
}

# create a subnet for the instance on alicloud
# @see: https://registry.terraform.io/providers/aliyun/alicloud/latest/docs/resources/vswitch
resource "alicloud_vswitch" "default" {
  vswitch_name = "${var.prefix}-vswitch"
  vpc_id       = var.vpc.id
  cidr_block   = cidrsubnet(var.vpc.cidr_block, 8, var.vswitch_netnum)
  zone_id      = sort(data.alicloud_zones.instance_availability.ids)[0]
}

# elastic ip
# @see: https://registry.terraform.io/providers/aliyun/alicloud/latest/docs/resources/eip_address
# TODO: check if isp needs special setting for China (https://registry.terraform.io/providers/aliyun/alicloud/latest/docs/resources/eip_address#isp)
resource "alicloud_eip_address" "default" {
  address_name         = "${var.prefix}-eip"
  resource_group_id    = var.resource_group.id
  bandwidth            = "100"
  internet_charge_type = "PayByTraffic"
}

# create instance
# @see: https://registry.terraform.io/providers/aliyun/alicloud/latest/docs/resources/instance
resource "alicloud_instance" "default" {
  instance_name     = "${var.prefix}-vm"
  resource_group_id = var.resource_group.id

  host_name            = "${var.prefix}-vm"
  instance_type        = var.instance_type
  internet_charge_type = "PayByTraffic"
  stopped_mode         = "StopCharging"
  image_id             = "ubuntu_20_04_x64_20G_alibase_20230907.vhd"
  key_name             = var.key_pair.key_pair_name
  vswitch_id           = alicloud_vswitch.default.id
  security_groups      = alicloud_security_group.default.*.id
  availability_zone    = sort(data.alicloud_zones.instance_availability.ids)[0]

  # @see: https://www.alibabacloud.com/help/en/ecs/user-guide/essds
  system_disk_performance_level = "PL1"
  system_disk_size              = var.disk_size_gib
  system_disk_category          = "cloud_auto"

  # by default, only root user exists in ubuntu image
  # create a new user, add public key, add user to sudoers
  user_data = base64encode(<<-EOF
    #!/bin/bash
    USERNAME="ubuntu"
    useradd -m -d /home/$USERNAME -s /bin/bash $USERNAME
    mkdir /home/$USERNAME/.ssh
    cat /root/.ssh/authorized_keys >> /home/$USERNAME/.ssh/authorized_keys
    cp /home/$USERNAME/.ssh/authorized_keys /home/$USERNAME/.ssh/authorized_keys.bak
    uniq /home/$USERNAME/.ssh/authorized_keys.bak > /home/$USERNAME/.ssh/authorized_keys
    chown -R $USERNAME:$USERNAME /home/$USERNAME
    echo "$USERNAME ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers
    EOF
  )
}

resource "alicloud_eip_association" "default" {
  instance_id   = alicloud_instance.default.id
  allocation_id = alicloud_eip_address.default.id
}

