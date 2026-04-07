output "isaac_workstation_ip" {
  value = var.isaac_workstation_enabled ? module.isaac_workstation[0].public_ip : "NA"
}

output "isaac_workstation_vm_id" {
  value = var.isaac_workstation_enabled ? module.isaac_workstation[0].vm_id : "NA"
}

output "ssh_key" {
  value     = module.common.ssh_key.private_key_pem
  sensitive = true
}

output "cloud" {
  value = "azure"
}
