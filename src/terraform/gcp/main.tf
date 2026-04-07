terraform {
  required_version = ">= 1.3.5"
  backend "local" {}
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 4.57.0"
    }
  }
}

provider "google" {
  project = var.project
  zone    = var.zone
}

# automatically enables the Compute Engine API
resource "google_project_service" "compute_engine" {
  project            = var.project
  service            = "compute.googleapis.com"
  disable_on_destroy = false
}

module "isaac_workstation" {
  source             = "./ovkit"
  count              = var.isaac_workstation_enabled ? 1 : 0
  isaac_enabled      = true
  prefix             = "${var.prefix}-${var.deployment_name}-isaac-workstation"
  deployment_name    = var.deployment_name
  public_key_openssh = tls_private_key.ssh_key.public_key_openssh
  instance_type      = var.isaac_workstation_instance_type
  gpu_count          = var.isaac_workstation_gpu_count
  gpu_type           = var.isaac_workstation_gpu_type
  ssh_port           = var.ssh_port
  ingress_cidrs      = var.ingress_cidrs
  boot_disk_type     = var.boot_disk_type
  os_username        = var.os_username
}
