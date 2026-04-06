packer {
  required_plugins {
    amazon = {
      source  = "github.com/hashicorp/amazon"
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

variable "aws_access_key_id" {
  default = env("AWS_ACCESS_KEY_ID")

  validation {
    condition     = can(regex("^[A-Z0-9]{20}$", var.aws_access_key_id))
    error_message = <<EOF
Invalid AWS Access Key ID. To fix this:
  - Set AWS_ACCESS_KEY_ID environment variable.
  - Add -var=aws_access_key_id=... argument.
EOF
  }
}

variable "aws_secret_access_key" {
  default = env("AWS_SECRET_ACCESS_KEY")

  validation {
    condition     = can(regex("^[A-Za-z0-9/+]{40}$", var.aws_secret_access_key))
    error_message = <<EOF
Invalid AWS Secret Access Key. To fix this:
  - Set AWS_SECRET_ACCESS_KEY environment variable.
  - Add -var=aws_secret_access_key=... argument.
EOF
  }
}

variable "aws_session_token" {
  default = env("AWS_SESSION_TOKEN")
}

variable "image_name" {
  default = "$PREFIX.$VERSION"
}

variable skip_tags {
  default = "skip_in_image"
}

variable "skip_create_ami" {
  default = false
}

variable "aws_region" {
  default = "us-east-1"
}

variable "instance_type" {
  default = "g6e.2xlarge"
}

variable "isaacsim" {
  default = "v6.0.0-dev2"
}

variable "isaaclab" {
  default = "v3.0.0-beta"
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

data "amazon-ami" "isaac_workstation_ami" {
  most_recent = true
  owners      = ["099720109477"] # Canonical
  region      = "${var.aws_region}"
  # @ see https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_DescribeImages.html
  filters = {
    virtualization-type = "hvm"
    root-device-type    = "ebs"
    name                = "ubuntu/images/*/ubuntu-*-22.04-amd64-server-*"
  }
}

locals {
  expanded_image_name = replace(replace(var.image_name, "$VERSION", var.version), "$PREFIX", "isaacautomator.isaacworkstation")
}

source "amazon-ebs" "isaac-workstation" {
  ami_name      = "${local.expanded_image_name}"
  access_key    = "${var.aws_access_key_id}"
  secret_key    = "${var.aws_secret_access_key}"
  token         = "${var.aws_session_token}"
  instance_type = "${var.instance_type}"
  region        = "${var.aws_region}"
  source_ami    = data.amazon-ami.isaac_workstation_ami.id
  ssh_username  = "ubuntu"
  encrypt_boot  = false

  force_delete_snapshot = true
  snapshot_timeout      = "2h"

  run_volume_tags = {
    Name       = "${local.expanded_image_name}.run_volume"
    Deployment = "${local.expanded_image_name}"
  }

  launch_block_device_mappings {
    delete_on_termination = true

    device_name = "/dev/sda1"
    encrypted   = false
    volume_size = 64
  }

  tags = {
    Name       = "${local.expanded_image_name}"
    Deployment = "${local.expanded_image_name}"
  }

  # skip image creation for some cases
  skip_create_ami = var.skip_create_ami
}

build {
  sources = ["source.amazon-ebs.isaac-workstation"]

  provisioner "ansible" {
    use_proxy     = false
    groups        = ["isaac-workstation"]
    playbook_file = "/app/src/ansible/isaac-workstation.yaml"
    ansible_env_vars = [
      "ANSIBLE_CONFIG=/app/src/ansible/ansible.cfg"
    ]
    extra_arguments = [
      "--skip-tags", "${var.skip_tags}",
      "--extra-vars", "cloud='aws' deployment_name='aws_image' isaacsim_git_checkpoint='${var.isaacsim}' isaaclab_git_checkpoint='${var.isaaclab}' vnc_password='${var.vnc_password}' system_user_password='${var.system_user_password}' in_china=${var.in_china} generic_driver_apt_package='nvidia-driver-580-server' uploads_dir='/home/ubuntu/uploads' results_dir='/home/ubuntu/results' workspace_dir='/home/ubuntu/workspace'"
    ]
  }
}
