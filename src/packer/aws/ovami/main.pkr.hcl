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

variable "image_name" {
  default = "$PREFIX.ovami_image.$VERSION"
}

variable "ngc_api_key" {
  default = env("NGC_API_KEY")
}

variable skip_tags {
  default = "skip_in_ovami"
}

variable "skip_create_ami" {
  default = false
}

variable "aws_region" {
  default = "us-east-1"
}

variable "system_user_password" {
  type = string
}

variable "vnc_password" {
  type = string
}

data "amazon-ami" "ovami" {
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
  expanded_image_name = replace(replace(var.image_name, "$VERSION", var.version), "$PREFIX", "isa.packer")
}

source "amazon-ebs" "ovami" {
  ami_name      = "${local.expanded_image_name}"
  access_key    = "${var.aws_access_key_id}"
  secret_key    = "${var.aws_secret_access_key}"
  instance_type = "g5.4xlarge"
  region        = "${var.aws_region}"
  source_ami    = data.amazon-ami.ovami.id
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
  sources = ["source.amazon-ebs.ovami"]

  provisioner "ansible" {
    use_proxy     = false
    groups        = ["ovami"]
    playbook_file = "/app/src/ansible/ovami.yml"
    ansible_env_vars = [
      "ANSIBLE_CONFIG=/app/src/ansible/ansible.cfg"
    ]
    extra_arguments = [
      "--skip-tags", "${var.skip_tags}",
      "--extra-vars", "cloud='aws' deployment_name='aws_image' system_user_password='${var.system_user_password}' vnc_password='${var.vnc_password}'"
    ]
  }

  # add cleanup steps
  # @see https://docs.aws.amazon.com/imagebuilder/latest/userguide/security-best-practices.html
  provisioner "shell" {
    # @see https://developer.hashicorp.com/packer/docs/provisioners/shell#sudo-example
    execute_command = "echo 'packer' | sudo -S sh -c '{{ .Vars }} {{ .Path }}'"
    inline = [
      "sudo shred -zufv /etc/sudoers.d/90-cloud-init-users 2>&1 || true",
      "sudo shred -zufv /etc/locale.conf 2>&1 || true",
      "sudo shred -zufv /var/log/cloud-init.log 2>&1 || true",
      "sudo shred -zufv /var/log/cloud-init-output.log 2>&1 || true",
      "sudo shred -zufv /etc/.updated 2>&1 || true",
      "sudo shred -zufv /etc/aliases.db 2>&1 || true",
      "sudo shred -zufv /etc/hostname 2>&1 || true",
      "sudo shred -zufv /var/lib/misc/postfix.aliasesdb-stamp 2>&1 || true",
      "sudo shred -zufv /var/lib/postfix/master.lock 2>&1 || true",
      "sudo shred -zufv /var/spool/postfix/pid/master.pid 2>&1 || true",
      "sudo shred -zufv /var/.updated 2>&1 || true",
      "sudo shred -zufv /var/cache/yum/x86_64/2/.gpgkeyschecked.yum 2>&1 || true",
      "sudo shred -zufv /etc/ssh/ssh_host_rsa_key 2>&1 || true",
      "sudo shred -zufv /etc/ssh/ssh_host_rsa_key.pub 2>&1 || true",
      "sudo shred -zufv /etc/ssh/ssh_host_ecdsa_key 2>&1 || true",
      "sudo shred -zufv /etc/ssh/ssh_host_ecdsa_key.pub 2>&1 || true",
      "sudo shred -zufv /etc/ssh/ssh_host_ed25519_key 2>&1 || true",
      "sudo shred -zufv /etc/ssh/ssh_host_ed25519_key.pub 2>&1 || true",
      "sudo shred -zufv /root/.ssh/authorized_keys 2>&1 || true",
      "sudo shred -zufv /home/ubuntu/.ssh/authorized_keys 2>&1 || true",
      "sudo shred -zufv /var/log/audit/audit.log 2>&1 || true",
      "sudo shred -zufv /var/log/boot.log 2>&1 || true",
      "sudo shred -zufv /var/log/dmesg 2>&1 || true",
      "sudo shred -zufv /var/log/cron 2>&1 || true",
      "sudo shred -zufv /var/log/amazon/ssm/* 2>&1 || true"
    ]
  }
}
