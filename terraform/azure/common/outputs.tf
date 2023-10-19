output "rg" {
  value = azurerm_resource_group.isa_rg
}

output "vnet" {
  value = azurerm_virtual_network.isa_network
}

output "subnet" {
  value = azurerm_subnet.isa_subnet
}

output "ssh_key" {
  value = tls_private_key.ssh_key
}
