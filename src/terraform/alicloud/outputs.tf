
output "cloud" {
  value = "alicloud"
}

output "ssh_key" {
  value     = tls_private_key.ssh_key.private_key_pem
  sensitive = true
}


output "isaac_ip" {
  value = try(var.isaac_enabled ? module.isaac[0].public_ip : "NA", "NA")
}

output "isaac_vm_id" {
  value = try(var.isaac_enabled ? module.isaac[0].vm_id : "NA", "NA")
}

