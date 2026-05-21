packer {
  required_plugins {
    azure = {
      source  = "github.com/hashicorp/azure"
      version = "~> 2"
    }
    ansible = {
      source  = "github.com/hashicorp/ansible"
      version = "~> 1"
    }
  }
}

# vars can be set either from environment or the command line

variable "version" {
  default = env("VERSION")

  validation {
    condition     = can(regex("^v\\d+\\.\\d+\\.\\d+(\\-[a-z0-9\\-]+)?$", var.version))
    error_message = <<EOF
Invalid version. To fix this:
  - Set VERSION environment variable.
  - Add -var=version=... argument.
EOF
  }
}

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

# Resource group where the captured managed image will be stored.
variable "managed_image_resource_group_name" {
  default = "isaac_automator.packer"
}

variable "image_name" {
  default = "$PREFIX.$VERSION"
}

variable skip_tags {
  default = "skip_in_image"
}

variable skip_create_image {
  default = false
}

variable "azure_location" {
  default = "westus3"
}

variable "vm_size" {
  default = "Standard_NV36adms_A10_v5"
}

variable "isaacsim" {
  default = "v6.0.0-dev2"
}

variable "isaaclab" {
  default = "v3.0.0-beta"
}

variable "isaaclab_arena" {
  default = "release/0.1.1"
}

variable "vnc_password" {
  default = ""
}

variable "system_user_password" {
  default = ""
}

variable "in_china" {
  default = false
}

locals {
  expanded_image_name = replace(replace(var.image_name, "$VERSION", var.version), "$PREFIX", "isaac_automator.isaacworkstation")
}

# Uses credentials from `az login` (Azure CLI). The image-azure script logs
# in and exports AZURE_SUBSCRIPTION_ID before invoking packer.
# @see https://developer.hashicorp.com/packer/integrations/hashicorp/azure/latest/components/builder/arm
source "azure-arm" "isaac-workstation" {
  use_azure_cli_auth = true
  subscription_id    = "${var.azure_subscription_id}"

  image_offer     = "0001-com-ubuntu-server-jammy"
  image_publisher = "Canonical"
  image_sku       = "22_04-lts-gen2"

  location = "${var.azure_location}"
  vm_size  = "${var.vm_size}"
  os_type  = "Linux"
  os_disk_size_gb = 64

  ssh_username = "ubuntu"

  managed_image_resource_group_name = "${var.managed_image_resource_group_name}"
  managed_image_name                = "${local.expanded_image_name}"

  azure_tags = {
    Name       = "${local.expanded_image_name}"
    Deployment = "${local.expanded_image_name}"
  }

  skip_create_image = var.skip_create_image
}

build {
  sources = ["source.azure-arm.isaac-workstation"]

  provisioner "ansible" {
    use_proxy     = false
    groups        = ["isaac-workstation"]
    playbook_file = "/app/src/ansible/isaac-workstation.yaml"
    ansible_env_vars = [
      "ANSIBLE_CONFIG=/app/src/ansible/ansible.cfg"
    ]
    extra_arguments = [
      "--skip-tags", "${var.skip_tags}",
      "--extra-vars", "cloud='azure' deployment_name='azure_image' isaacsim_git_checkpoint='${var.isaacsim}' isaaclab_git_checkpoint='${var.isaaclab}' isaaclab_arena_git_checkpoint='${var.isaaclab_arena}' vnc_password='${var.vnc_password}' system_user_password='${var.system_user_password}' in_china=${var.in_china} uploads_dir='/home/ubuntu/uploads' results_dir='/home/ubuntu/results' workspace_dir='/home/ubuntu/workspace'"
    ]
  }

  provisioner "shell" {
    inline = [
      "sudo rm -rf /tmp/* /var/tmp/*",
      "sudo journalctl --vacuum-size=10M",
      "sudo waagent -deprovision+user -force",
    ]
  }
}
