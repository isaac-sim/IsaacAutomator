# region copyright
# Copyright 2023 NVIDIA Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# endregion

from typing import Any, Dict

c: Dict[str, Any] = {}

# paths
c["app_dir"] = "/app"
c["state_dir"] = "/app/state"
c["results_dir"] = "/app/results"
c["uploads_dir"] = "/app/uploads"
c["tests_dir"] = "/app/src/tests"
c["ansible_dir"] = "/app/src/ansible"
c["terraform_dir"] = "/app/src/terraform"

# app image name
c["app_image_name"] = "isa"

# gcp driver
# @see https://cloud.google.com/compute/docs/gpus/grid-drivers-table
c[
    "gcp_driver_url"
] = "https://storage.googleapis.com/nvidia-drivers-us-public/GRID/vGPU16.2/NVIDIA-Linux-x86_64-535.129.03-grid.run"

# aws/alicloud driver
c["generic_driver_apt_package"] = "nvidia-driver-535-server"

# default remote dirs
c["default_remote_uploads_dir"] = "/home/ubuntu/uploads"
c["default_remote_results_dir"] = "/home/ubuntu/results"
c["default_remote_workspace_dir"] = "/home/ubuntu/workspace"

# defaults

# --isaac-image
c["default_isaac_image"] = "nvcr.io/nvidia/isaac-sim:2023.1.1"

# --ssh-port
c["default_ssh_port"] = 22

# --from-image
c["azure_default_from_image"] = False
c["aws_default_from_image"] = False

# --omniverse-user
c["default_omniverse_user"] = "omniverse"

# --remote-dir
c["default_remote_uploads_dir"] = "/home/ubuntu/uploads"
c["default_remote_results_dir"] = "/home/ubuntu/results"

# --isaac-instance-type
c["aws_default_isaac_instance_type"] = "g5.2xlarge"
# str, 1-index in DeployAzureCommand.AZURE_OVKIT_INSTANCE_TYPES
c["azure_default_isaac_instance_type"] = "2"
c["gcp_default_isaac_instance_type"] = "g2-standard-8"
c["alicloud_default_isaac_instance_type"] = "ecs.gn7i-c16g1.4xlarge"

# --isaac-gpu-count
c["gcp_default_isaac_gpu_count"] = 1

# --region
c["alicloud_default_region"] = "us-east-1"

# --prefix for the created cloud resources
c["default_prefix"] = "isa"

# --oige
c["default_oige_git_checkpoint"] = "main"

# --orbit
c["default_orbit_git_checkpoint"] = "devel"
