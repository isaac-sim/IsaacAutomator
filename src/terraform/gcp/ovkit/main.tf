locals {
  # gcloud compute images list --filter="name~'ubuntu'"
  # boot_image     = "ubuntu-1804-bionic-v20230308"
  # boot_image     = "ubuntu-2004-focal-v20230302"
  boot_image     = "ubuntu-2204-jammy-v20240519"
  boot_disk_size = 255
  os_username    = "ubuntu"
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
      image = local.boot_image
      size  = local.boot_disk_size
      # @see https://cloud.google.com/compute/docs/disks
      type = "pd-ssd"
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
    access_config {}
  }
}

