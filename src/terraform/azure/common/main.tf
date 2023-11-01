# resource group
resource "azurerm_resource_group" "isa_rg" {
  name     = var.resource_group_name
  location = var.region
}

# virtual network
resource "azurerm_virtual_network" "isa_network" {
  name                = "${var.prefix}.vnet"
  address_space       = ["10.0.0.0/16"]
  location            = azurerm_resource_group.isa_rg.location
  resource_group_name = azurerm_resource_group.isa_rg.name
}

# subnet
resource "azurerm_subnet" "isa_subnet" {
  name                 = "${var.prefix}.subnet"
  resource_group_name  = azurerm_resource_group.isa_rg.name
  virtual_network_name = azurerm_virtual_network.isa_network.name
  address_prefixes     = ["10.0.1.0/24"]
}

# ssh key
resource "tls_private_key" "ssh_key" {
  algorithm = "RSA"
  rsa_bits  = 4096
}
