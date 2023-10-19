
resource "azurerm_public_ip" "public_ip" {
  name                = "${var.prefix}.public_ip"
  location            = var.rg.location
  resource_group_name = var.rg.name
  allocation_method   = "Static"
}

resource "azurerm_network_interface" "nic" {
  name                = "${var.prefix}.nic"
  location            = var.rg.location
  resource_group_name = var.rg.name

  ip_configuration {
    name                          = "${var.prefix}.nic_config"
    subnet_id                     = var.subnet.id
    private_ip_address_allocation = "Dynamic"
    public_ip_address_id          = azurerm_public_ip.public_ip.id
  }
}

resource "azurerm_network_interface_security_group_association" "nic_sg_association" {
  network_interface_id      = azurerm_network_interface.nic.id
  network_security_group_id = azurerm_network_security_group.sg.id
}

resource "azurerm_linux_virtual_machine" "vm_from_scratch" {
  name                  = "${var.prefix}.vm"
  location              = var.rg.location
  resource_group_name   = var.rg.name
  network_interface_ids = [azurerm_network_interface.nic.id]
  size                  = var.vm_type

  # no docs, but https://github.com/hashicorp/terraform-provider-azurerm/issues/160#issuecomment-338666563
  os_disk {
    name                 = "${var.prefix}.os_disk"
    caching              = "ReadWrite"
    storage_account_type = "Premium_LRS" # Standard_LRS, StandardSSD_LRS, Premium_LRS
    disk_size_gb         = 256
  }

  # list all:
  # az vm image list --all --publisher Canonical --offer ubuntu-server --sku 20_04-lts | jq -c '.[] | select(.sku=="20_04-lts")'

  source_image_reference {
    publisher = "Canonical"
    offer     = "0001-com-ubuntu-server-focal"
    sku       = "20_04-lts-gen2"
    version   = "20.04.202301100"
  }

  computer_name                   = "isaac"
  admin_username                  = "ubuntu"
  disable_password_authentication = true

  admin_ssh_key {
    username   = "ubuntu"
    public_key = var.ssh_key.public_key_openssh
  }

  count = var.from_image ? 0 : 1
}

resource "azurerm_linux_virtual_machine" "vm_from_image" {
  name                  = "${var.prefix}.vm"
  location              = var.rg.location
  resource_group_name   = var.rg.name
  network_interface_ids = [azurerm_network_interface.nic.id]
  size                  = var.vm_type

  # no docs, but https://github.com/hashicorp/terraform-provider-azurerm/issues/160#issuecomment-338666563
  os_disk {
    name                 = "${var.prefix}.os_disk"
    caching              = "ReadWrite"
    storage_account_type = "Premium_LRS" # Standard_LRS, StandardSSD_LRS, Premium_LRS
    disk_size_gb         = 256
  }

  # TODO: use public image
  # TODO: update image name
  source_image_id = "/subscriptions/4ca485f9-4cdf-4749-9d14-320dd780fc1c/resourceGroups/isa.PACKER/providers/Microsoft.Compute/images/isa.isaac_image"

  computer_name                   = "isaac"
  admin_username                  = "ubuntu"
  disable_password_authentication = true

  admin_ssh_key {
    username   = "ubuntu"
    public_key = var.ssh_key.public_key_openssh
  }

  count = var.from_image ? 1 : 0
}
