packer {
  required_plugins {
    googlecompute = {
      source  = "github.com/hashicorp/googlecompute"
      version = "~> 1"
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

variable "gcp_project" {
  default = env("GCP_PROJECT")

  validation {
    condition     = length(var.gcp_project) > 0
    error_message = <<EOF
Required variable "gcp_project" is not set. To fix this:
 - Set GCP_PROJECT environment variable.
 - Add -var=gcp_project=... argument.
EOF
  }
}

variable "gcp_zone" {
  default = "us-central1-a"
}

variable "instance_type" {
  default = "g2-standard-8"
}

# GCP requires the accelerator block on instances using a GPU image, but the
# image itself does not need a specific GPU attached during build. We still
# attach one so NVIDIA drivers can be validated end-to-end during Ansible.
variable "gpu_type" {
  default = "nvidia-l4"
}

variable "gpu_count" {
  default = 1
}

variable "image_name" {
  default = "$PREFIX-$VERSION"
}

variable skip_tags {
  default = "skip_in_image"
}

variable skip_create_image {
  default = false
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
  # GCE image names must be lowercase and may contain only letters, numbers, and dashes.
  # Replace the $VERSION placeholder, normalize the version string, and lowercase the result.
  raw_image_name      = replace(replace(var.image_name, "$VERSION", var.version), "$PREFIX", "isaac-automator-isaacworkstation")
  expanded_image_name = lower(replace(local.raw_image_name, ".", "-"))
}

# Uses application default credentials. The image-gcp script runs
# `gcloud auth application-default login` and exports GCP_PROJECT.
# @see https://developer.hashicorp.com/packer/integrations/hashicorp/googlecompute
source "googlecompute" "isaac-workstation" {
  project_id   = "${var.gcp_project}"
  zone         = "${var.gcp_zone}"
  machine_type = "${var.instance_type}"

  source_image_family  = "ubuntu-2204-lts"
  source_image_project_id = ["ubuntu-os-cloud"]

  image_name        = "${local.expanded_image_name}"
  image_family      = "isaac-automator-isaacworkstation"
  image_description = "Isaac Automator workstation image (${var.version})"

  disk_size = 255
  disk_type = "pd-ssd"

  ssh_username = "ubuntu"

  # GPUs require TERMINATE on host maintenance.
  on_host_maintenance = "TERMINATE"

  accelerator_type  = "projects/${var.gcp_project}/zones/${var.gcp_zone}/acceleratorTypes/${var.gpu_type}"
  accelerator_count = var.gpu_count

  labels = {
    deployment = "gcp_image"
  }

  skip_create_image = var.skip_create_image
}

build {
  sources = ["source.googlecompute.isaac-workstation"]

  provisioner "ansible" {
    use_proxy     = false
    groups        = ["isaac-workstation"]
    playbook_file = "/app/src/ansible/isaac-workstation.yaml"
    ansible_env_vars = [
      "ANSIBLE_CONFIG=/app/src/ansible/ansible.cfg"
    ]
    extra_arguments = [
      "--skip-tags", "${var.skip_tags}",
      "--extra-vars", "cloud='gcp' deployment_name='gcp_image' isaacsim_git_checkpoint='${var.isaacsim}' isaaclab_git_checkpoint='${var.isaaclab}' isaaclab_arena_git_checkpoint='${var.isaaclab_arena}' vnc_password='${var.vnc_password}' system_user_password='${var.system_user_password}' in_china=${var.in_china} uploads_dir='/home/ubuntu/uploads' results_dir='/home/ubuntu/results' workspace_dir='/home/ubuntu/workspace'"
    ]
  }

  provisioner "shell" {
    inline = [
      "sudo rm -rf /tmp/* /var/tmp/*",
      "sudo journalctl --vacuum-size=10M",
      "sudo dd if=/dev/zero of=/EMPTY bs=1M || true",
      "sudo rm -f /EMPTY",
      "sync"
    ]
  }
}
