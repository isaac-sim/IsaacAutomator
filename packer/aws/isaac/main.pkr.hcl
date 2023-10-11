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

variable "image_name" {
  default = "$PREFIX.isaac_image.$VERSION"
}

variable "ngc_api_key" {
  default = env("NGC_API_KEY")
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

data "amazon-ami" "isaac_instance_ami" {
  most_recent = true
  owners      = ["099720109477"] # Canonical
  region      = "${var.aws_region}"
  # @ see https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_DescribeImages.html
  filters = {
    virtualization-type = "hvm"
    root-device-type    = "ebs"
    name                = "ubuntu/images/*/ubuntu-*-20.04-amd64-server-*"
  }
}

locals {
  expanded_image_name = replace(replace(var.image_name, "$VERSION", var.version), "$PREFIX", "ovcloud.packer")
}

source "amazon-ebs" "isaac" {
  ami_name      = "${local.expanded_image_name}"
  access_key    = "${var.aws_access_key_id}"
  secret_key    = "${var.aws_secret_access_key}"
  instance_type = "g5.2xlarge"
  region        = "${var.aws_region}"
  source_ami    = data.amazon-ami.isaac_instance_ami.id
  ssh_username  = "ubuntu"
  encrypt_boot  = false

  force_delete_snapshot = true

  run_volume_tags = {
    Name       = "${local.expanded_image_name}.run_volume"
    Deployment = "${local.expanded_image_name}"
  }

  launch_block_device_mappings {
    delete_on_termination = true

    device_name = "/dev/sda1"
    encrypted   = false
    volume_size = 31
  }

  tags = {
    Name       = "${local.expanded_image_name}"
    Deployment = "${local.expanded_image_name}"
  }

  # skip image creation for some cases
  skip_create_ami = var.skip_create_ami
}

build {
  sources = ["source.amazon-ebs.isaac"]

  provisioner "ansible" {
    use_proxy     = false
    groups        = ["isaac"]
    playbook_file = "/app/ansible/isaac.yml"
    ansible_env_vars = [
      "ANSIBLE_CONFIG=/app/ansible/ansible.cfg"
    ]
    extra_arguments = [
      "--skip-tags", "${var.skip_tags}",
      "--extra-vars", "cloud='aws' deployment_name='aws_image' ngc_api_key='${var.ngc_api_key} omniverse_user='''"
    ]
  }
}
