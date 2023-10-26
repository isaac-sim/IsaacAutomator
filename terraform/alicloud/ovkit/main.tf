# find zones where instance is available

data "alicloud_zones" "zones_ds" {
  available_instance_type = var.instance_type
  available_disk_category = "cloud_ssd"
}

