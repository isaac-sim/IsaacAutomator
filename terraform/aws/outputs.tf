
output "ssh_key" {
  value     = module.common.ssh_key.private_key_pem
  sensitive = true
}

output "cloud" {
  value = "aws"
}

output "isaac_ip" {
  value = var.isaac_enabled ? module.isaac[0].public_ip : "NA"
}

output "ovami_ip" {
  value = var.ovami_enabled ? module.ovami[0].public_ip : "NA"
}

