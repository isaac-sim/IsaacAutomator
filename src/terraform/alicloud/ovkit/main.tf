# find zones where instance is available

data "alicloud_zones" "instance_availability" {
  available_instance_type = var.instance_type
  available_disk_category = var.system_disk_category
}

# create a subnet for the instance on alicloud
# https://registry.terraform.io/providers/aliyun/alicloud/latest/docs/resources/vswitch
resource "alicloud_vswitch" "default" {
  vpc_id       = var.vpc.id
  cidr_block   = cidrsubnet(var.vpc.cidr_block, 8, var.vswitch_netnum)
  vswitch_name = "${var.prefix}-vswitch"
  zone_id      = sort(data.alicloud_zones.instance_availability.ids)[0]
}

# create instance
# https://registry.terraform.io/providers/aliyun/alicloud/latest/docs/resources/instance

resource "alicloud_instance" "ovkit_vm" {
  instance_name = "${var.prefix}-vm"
  instance_type = var.instance_type

  resource_group_id    = var.resource_group.id
  availability_zone    = sort(data.alicloud_zones.instance_availability.ids)[0]
  security_groups      = alicloud_security_group.default.*.id
  vswitch_id           = alicloud_vswitch.default.id
  image_id             = "ubuntu_18_04_64_20G_alibase_20190624.vhd"
  internet_charge_type = "PayByTraffic"

  system_disk_category          = var.system_disk_category
  system_disk_size              = var.system_disk_size
  system_disk_performance_level = "PL1" # https://www.alibabacloud.com/help/en/ecs/user-guide/essds
  system_disk_encrypted         = false

  host_name = "${var.prefix}-vm"

  key_name = var.key_pair.key_pair_name
}

#  + resource "alicloud_instance" "ovkit_vm" {
#       + availability_zone                  = "us-east-1a"
#       + cpu                                = (known after apply)
#       + credit_specification               = (known after apply)
#       + deletion_protection                = false
#       + deployment_set_group_no            = (known after apply)
#       + dry_run                            = false
#       + host_name                          = (known after apply)
#       + http_endpoint                      = (known after apply)
#       + http_put_response_hop_limit        = (known after apply)
#       + http_tokens                        = (known after apply)
#       + id                                 = (known after apply)
#       + image_id                           = "ubuntu_18_04_64_20G_alibase_20190624.vhd"
#       + instance_charge_type               = "PostPaid"
#       + instance_name                      = "isa-ali2-isaac-vm"
#       + instance_type                      = "ecs.gn7i-c16g1.4xlarge"
#       + internet_max_bandwidth_in          = (known after apply)
#       + internet_max_bandwidth_out         = 0
#       + ipv6_address_count                 = (known after apply)
#       + ipv6_addresses                     = (known after apply)
#       + key_name                           = (known after apply)
#       + maintenance_action                 = (known after apply)
#       + memory                             = (known after apply)
#       + network_interface_id               = (known after apply)
#       + os_name                            = (known after apply)
#       + os_type                            = (known after apply)
#       + primary_ip_address                 = (known after apply)
#       + private_ip                         = (known after apply)
#       + public_ip                          = (known after apply)
#       + role_name                          = (known after apply)
#       + secondary_private_ip_address_count = (known after apply)
#       + secondary_private_ips              = (known after apply)
#       + security_groups                    = (known after apply)
#       + spot_duration                      = (known after apply)
#       + spot_strategy                      = (known after apply)
#       + status                             = (known after apply)
#       + stopped_mode                       = (known after apply)
#       + subnet_id                          = (known after apply)
#       + system_disk_category               = "cloud_efficiency"
#       + system_disk_id                     = (known after apply)
#       + system_disk_performance_level      = (known after apply)
#       + system_disk_size                   = 40
#       + volume_tags                        = (known after apply)
#       + vswitch_id                         = (known after apply)
#     }
