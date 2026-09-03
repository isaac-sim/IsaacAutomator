# region copyright
# Copyright 2023-2026 NVIDIA Corporation
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

from typing import Any

c: dict[str, Any] = {}

# paths
c["app_dir"] = "/app"
c["state_dir"] = "/app/state"
c["results_dir"] = "/app/results"
c["uploads_dir"] = "/app/uploads"
c["tests_dir"] = "/app/src/tests"
c["ansible_dir"] = "/app/src/ansible"
c["terraform_dir"] = "/app/src/terraform"

# app image name
c["app_image_name"] = "isaac_automator"


# aws/alicloud driver
c["generic_driver_apt_package"] = "nvidia-driver-580-server"

# default ssh user
c["default_ssh_user"] = "ubuntu"

# default remote dirs
c["default_remote_uploads_dir"] = f"/home/{c['default_ssh_user']}/uploads"
c["default_remote_results_dir"] = f"/home/{c['default_ssh_user']}/results"
c["default_remote_workspace_dir"] = f"/home/{c['default_ssh_user']}/workspace"

# defaults

# --ssh-port
c["default_ssh_port"] = 22

# --from-image
c["azure_default_from_image"] = False
c["aws_default_from_image"] = False

# --isaac-workstation-instance-type
c["aws_default_isaac_workstation_instance_type"] = "g6e.2xlarge"
# str, 1-index in DeployAzureCommand.AZURE_OVKIT_INSTANCE_TYPES
c["azure_default_isaac_workstation_instance_type"] = "Standard_NV36ads_A10_v5"
c["gcp_default_isaac_workstation_instance_type"] = "g2-standard-8"
c["alicloud_default_isaac_workstation_instance_type"] = "ecs.gn7i-c16g1.4xlarge"

# --isaac-workstation-gpu-count
c["gcp_default_isaac_workstation_gpu_count"] = 1

# --region
c["alicloud_default_region"] = "us-east-1"

# --prefix for the created cloud resources
c["default_prefix"] = "isaacautomator"

# --isaacsim / --isaaclab / --isaaclab-arena
# "latest" -> auto-detect the latest release at deploy time (see git_ref_callback):
# highest version across the repo's tags + release/* branches, prereleases included
# (so it tracks e.g. a 3.0.0-beta line, not an older stable), branch wins on a tie.
# Can be overridden with an explicit git ref or "no" to skip.
c["default_isaaclab_git_checkpoint"] = "latest"
c["default_isaaclab_arena_git_checkpoint"] = "latest"
c["default_isaacsim_git_checkpoint"] = "latest"

# git repos used to validate / auto-detect the --isaacsim/--isaaclab/--isaaclab-arena
# refs before deploy (mirror of the ansible role defaults; keep both in sync if a repo moves).
# Each can be overridden per deployment with --isaacsim-git-repo/--isaaclab-git-repo/
# --isaaclab-arena-git-repo, or inline as "<repo url>@<ref>" in the ref option itself,
# to install from a fork or an internal repo (NVBugs 6696514).
c["isaacsim_git_repo"] = "https://github.com/isaac-sim/IsaacSim.git"
c["isaaclab_git_repo"] = "https://github.com/isaac-sim/IsaacLab.git"
c["isaaclab_arena_git_repo"] = "https://github.com/isaac-sim/IsaacLab-Arena.git"

# --ingress-cidrs
# empty value will be replaced with the current public IP
c["default_ingress_cidrs"] = "0.0.0.0/0"

# --demos
# Out-of-the-box demos to install on the workstation, exposed as double-click
# desktop shortcuts. Comma-separated list of names from c["demos"], or "no".
c["default_demos"] = "no"

# Demo registry. Each demo lists the apps it depends on (by the deploy option
# name); selecting a demo auto-enables those apps if they were left off, using
# their default git ref. Names here must match the demos role tasks.
c["demos"] = {
    "quadruped-locomotion": {
        "description": "Train an ANYmal-D quadruped to walk using RSL-RL in Isaac Lab.",
        "requires": ["isaacsim", "isaaclab"],
    },
    "humanoid-locomotion": {
        "description": "Train a Unitree G1 humanoid to walk using RSL-RL in Isaac Lab.",
        "requires": ["isaacsim", "isaaclab"],
    },
    "franka-manipulation": {
        "description": "Train a Franka arm to reach targets using RSL-RL in Isaac Lab.",
        "requires": ["isaacsim", "isaaclab"],
    },
}
