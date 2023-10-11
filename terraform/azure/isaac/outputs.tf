output "public_ip" {
  value = try(var.from_image ? azurerm_linux_virtual_machine.vm_from_image[0].public_ip_address : azurerm_linux_virtual_machine.vm_from_scratch[0].public_ip_address, "NA")
}
