packer {
  required_plugins {
    amazon = {
      source  = "github.com/hashicorp/azure"
      version = "~> 1"
    }
    ansible = {
      source  = "github.com/hashicorp/ansible"
      version = "~> 1"
    }
  }
}

# vars can be set either from environment or the command line

variable "azure_subscription_id" {
  default = env("AZURE_SUBSCRIPTION_ID")

  validation {
    condition     = length(var.azure_subscription_id) > 0
    error_message = <<EOF
Required variable "azure_subscription_id" is not set. To fix this:
 - Set AZURE_SUBSCRIPTION_ID environment variable.
 - Add -var=azure_subscription_id=... argument.
EOF
  }
}

variable "azure_tenant_id" {
  default = env("AZURE_TENANT_ID")

  validation {
    condition     = length(var.azure_tenant_id) > 0
    error_message = <<EOF
Required variable "azure_tenant_id" is not set. To fix this:
 - Set AZURE_TENANT_ID environment variable.
 - Add -var=azure_tenant_id=... argument.
EOF
  }
}

variable "azure_sp_client_id" {
  default = env("AZURE_SP_CLIENT_ID")

  validation {
    condition     = length(var.azure_sp_client_id) > 0
    error_message = <<EOF
Required variable "azure_tenant_id" is not set. To fix this:
 - Set AZURE_SP_CLIENT_ID environment variable.
 - Add -var=azure_sp_client_id=... argument.
EOF
  }
}

variable "azure_sp_client_secret" {
  default = env("AZURE_SP_CLIENT_SECRET")

  validation {
    condition     = length(var.azure_sp_client_secret) > 0
    error_message = <<EOF
Required variable "azure_sp_client_secret" is not set. To fix this:
 - Set AZURE_SP_CLIENT_SECRET environment variable.
 - Add -var=azure_sp_client_secret=... argument.
EOF
  }
}

variable "image_name" {
  default = "isaac_image"
}

variable "ngc_api_key" {
  default = env("NGC_CLI_API_KEY")
}

variable skip_tags {
  default = "skip_in_image"
}

variable skip_create_image {
  default = false
}

# for reference
# @see https://developer.hashicorp.com/packer/plugins/builders/azure/arm

source "azure-arm" "isaac" {
  azure_tags = {}

  client_id       = "${var.azure_sp_client_id}"
  client_secret   = "${var.azure_sp_client_secret}"
  subscription_id = "${var.azure_subscription_id}"
  tenant_id       = "${var.azure_tenant_id}"

  image_offer     = "0001-com-ubuntu-server-focal"
  image_publisher = "Canonical"
  image_sku       = "20_04-lts-gen2"
  image_version   = "20.04.202301100"

  location = "westus3"

  managed_image_resource_group_name = "isaac_automator.packer"
  managed_image_name                = "isaac_automator.${var.image_name}"

  vm_size = "Standard_NV36adms_A10_v5"
  os_type = "Linux"

  ssh_username = "ubuntu"

  skip_create_image = var.skip_create_image
}

build {
  sources = ["source.azure-arm.isaac"]

  provisioner "ansible" {
    use_proxy     = false
    groups        = ["isaac"]
    playbook_file = "/app/src/ansible/isaac.yml"
    ansible_env_vars = [
      "ANSIBLE_CONFIG=/app/src/ansible/ansible.cfg"
    ]
    extra_arguments = [
      "--skip-tags", "${var.skip_tags}",
      "--extra-vars", "cloud='azure' deployment_name='azure_image' ngc_api_key='${var.ngc_api_key}'"
    ]
  }

  provisioner "shell" {
    inline = ["sudo waagent -deprovision+user -force"]
  }
}
