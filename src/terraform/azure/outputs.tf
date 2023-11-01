output "isaac_ip" {
  value = var.isaac_enabled ? module.isaac[0].public_ip : "NA"
}

output "isaac_vm_id" {
  value = var.isaac_enabled ? module.isaac[0].vm_id : "NA"
}

# we cant have aws ami on azure, who could think
output "ovami_ip" {
  value = "NA"
}

output "ssh_key" {
  value     = module.common.ssh_key.private_key_pem
  sensitive = true
}

output "cloud" {
  value = "azure"
}
