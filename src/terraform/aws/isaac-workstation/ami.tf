
# finds available base image
data "aws_ami" "ami" {
  most_recent = true

  filter {
    name = "name"
    values = [
      var.from_image ? var.prebuilt_ami_name : var.base_ami_name
    ]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }

  owners = [
    "565494100184", # NVIDIA
    "099720109477", # Canonical
    "self"          # Customer
  ]
}
