# Configure the Azure provider
terraform {
  required_version = ">= 1.3.5"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 2.99"
    }
  }
}

provider "azurerm" {
  features {
    resource_group {
      prevent_deletion_if_contains_resources = true
    }

    virtual_machine {
      delete_os_disk_on_deletion     = true
      graceful_shutdown              = false
      skip_shutdown_and_force_delete = false
    }
  }
}

module "common" {
  source              = "./common"
  prefix              = "${var.prefix}.${var.deployment_name}"
  region              = var.region
  resource_group_name = var.resource_group_name
}

module "isaac" {
  source     = "./isaac"
  count      = var.isaac_enabled ? 1 : 0
  prefix     = "${var.prefix}.${var.deployment_name}.isaac"
  rg         = module.common.rg
  subnet     = module.common.subnet
  ssh_key    = module.common.ssh_key
  vm_type    = var.isaac_instance_type
  from_image = var.from_image
  ssh_port   = var.ssh_port
}
