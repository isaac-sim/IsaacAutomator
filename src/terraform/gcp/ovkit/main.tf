locals {
  # gcloud compute images list --filter="name~'ubuntu'"
  # boot_image     = "ubuntu-1804-bionic-v20230308"
  # boot_image     = "ubuntu-2004-focal-v20230302"
  boot_image     = "ubuntu-2204-jammy-v20251023"
  boot_disk_size = 255
  os_username    = var.os_username
}

# Latest image in the family created by ./image-gcp. Only resolved when
# --from-image is true, so deployments that don't use a pre-built image
# can still run in projects with no Isaac Automator images yet.
data "google_compute_image" "prebuilt" {
  count   = var.from_image ? 1 : 0
  family  = "isaac-automator-isaacworkstation"
  project = var.image_project
}

resource "google_compute_instance" "default" {
  name           = "${var.prefix}-vm"
  machine_type   = var.instance_type
  enable_display = false

  # allows to change instance type without destriying everything
  allow_stopping_for_update = true

  scheduling {
    # required when gpus are used
    on_host_maintenance = "TERMINATE"
  }

  boot_disk {
    auto_delete = true

    initialize_params {
      image = var.from_image ? data.google_compute_image.prebuilt[0].self_link : local.boot_image
      size  = local.boot_disk_size
      # @see https://cloud.google.com/compute/docs/disks
      type = var.boot_disk_type
    }
  }

  metadata = {
    ssh-keys = "${local.os_username}:${var.public_key_openssh}"
  }

  labels = {
    deployment = var.deployment_name
  }

  guest_accelerator {
    type  = var.gpu_type
    count = var.gpu_count
  }

  network_interface {
    network = google_compute_network.default.self_link
    access_config {
      nat_ip = google_compute_address.static_ip.address
    }
  }
}


