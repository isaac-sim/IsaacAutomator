output "rg" {
  value = azurerm_resource_group.ovcloud_rg
}

output "vnet" {
  value = azurerm_virtual_network.ovcloud_network
}

output "subnet" {
  value = azurerm_subnet.ovcloud_subnet
}

output "ssh_key" {
  value = tls_private_key.ssh_key
}
