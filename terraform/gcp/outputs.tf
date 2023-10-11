
output "cloud" {
  value = "gcp"
}

output "isaac_ip" {
  value = var.isaac_enabled ? module.isaac[0].public_ip : "NA"
}

output "ssh_key" {
  value     = tls_private_key.ssh_key.private_key_pem
  sensitive = true
}
