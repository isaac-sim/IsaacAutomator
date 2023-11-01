output "public_ip" {
  value = google_compute_instance.default.network_interface[0].access_config[0].nat_ip
}

output "vm_id" {
  value = google_compute_instance.default.id
}
