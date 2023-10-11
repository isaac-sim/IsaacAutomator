
resource "google_compute_network" "default" {
  name = "${var.prefix}-network"
}

# all egress
resource "google_compute_firewall" "egress" {
  name    = "${var.prefix}-fwrules-egress"
  network = google_compute_network.default.self_link

  allow {
    protocol = "all"
  }

  direction          = "EGRESS"
  destination_ranges = ["0.0.0.0/0"]
}

# ssh
resource "google_compute_firewall" "ssh" {
  name    = "${var.prefix}-fwrules-ssh"
  network = google_compute_network.default.self_link

  allow {
    protocol = "tcp"
    ports    = ["22"]
  }

  source_ranges = ["0.0.0.0/0"]
}

# nomachine
resource "google_compute_firewall" "nomachine" {
  name    = "${var.prefix}-fwrules-nomachine"
  network = google_compute_network.default.self_link

  allow {
    protocol = "udp"
    ports    = ["4000"]
  }

  allow {
    protocol = "tcp"
    ports    = ["4000"]
  }

  source_ranges = ["0.0.0.0/0"]
}

# vnc
resource "google_compute_firewall" "vnc" {
  name    = "${var.prefix}-fwrules-vnc"
  network = google_compute_network.default.self_link

  allow {
    protocol = "tcp"
    ports    = ["5900"]
  }

  source_ranges = ["0.0.0.0/0"]
}

# custom ssh port
resource "google_compute_firewall" "ssh_custom" {
  name    = "${var.prefix}-fwrules-ssh-custom"
  network = google_compute_network.default.self_link

  allow {
    protocol = "tcp"
    ports    = ["${var.ssh_port}"]
  }

  source_ranges = ["0.0.0.0/0"]
}
