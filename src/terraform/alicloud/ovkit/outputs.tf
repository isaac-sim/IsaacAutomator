output "public_ip" {
  value = alicloud_eip_address.default.ip_address
}

output "vm_id" {
  value = alicloud_instance.default.id
}
