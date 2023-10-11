resource "azurerm_network_security_group" "sg" {
  name                = "${var.prefix}.sg"
  location            = var.rg.location
  resource_group_name = var.rg.name

  security_rule {
    name                       = "SSH"
    priority                   = 1001
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "22"
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }

  security_rule {
    name                       = "NoMachine"
    priority                   = 102
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "*"
    source_port_range          = "*"
    destination_port_ranges    = ["4000"]
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }

  security_rule {
    name                       = "VNC"
    priority                   = 103
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "TCP"
    source_port_range          = "*"
    destination_port_ranges    = ["5900"]
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }
}

# security rule for custom ssh port
resource "azurerm_network_security_rule" "custom_ssh" {
  name                        = "Custom_SSH"
  priority                    = 104
  direction                   = "Inbound"
  access                      = "Allow"
  protocol                    = "Tcp"
  source_port_range           = "*"
  destination_port_range      = var.ssh_port
  source_address_prefix       = "*"
  destination_address_prefix  = "*"
  network_security_group_name = azurerm_network_security_group.sg.name
  resource_group_name         = var.rg.name
  count                       = var.ssh_port != 22 ? 1 : 0
}
