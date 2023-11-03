output "ssh_key" {
  value = tls_private_key.ssh_key
}

output "vpc" {
  value = alicloud_vpc.default
}

output "resource_group" {
  value = alicloud_resource_manager_resource_group.default
}

output "key_pair" {
  value = alicloud_ecs_key_pair.default
}
