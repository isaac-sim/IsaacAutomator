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


"""
Utils for AliCloud
"""

from src.python.utils import read_meta, shell_command


def alicloud_configure_cli(
    deployment_name,
    verbose=False,
):
    """
    Configure Aliyun CLI
    """
    meta = read_meta(deployment_name)

    aliyun_access_key = meta["params"]["aliyun_access_key"]
    aliyun_secret_key = meta["params"]["aliyun_secret_key"]
    region = meta["params"]["region"]

    shell_command(
        "aliyun configure set "
        + f"--access-key-id '{aliyun_access_key}'"
        + f" --access-key-secret '{aliyun_secret_key}'"
        + f" --region '{region}'",
        verbose=verbose,
        exit_on_error=True,
        capture_output=True,
    )


def alicloud_start_instance(vm_id, verbose=False):
    """
    Start VM
    """
    shell_command(
        f"aliyun ecs StartInstance --InstanceId '{vm_id}'",
        verbose=verbose,
        exit_on_error=True,
        capture_output=True,
    )


def alicloud_stop_instance(vm_id, verbose=False):
    """
    Stop VM
    """
    shell_command(
        f"aliyun ecs StopInstance --InstanceId '{vm_id}'",
        verbose=verbose,
        exit_on_error=True,
        capture_output=True,
    )


def alicloud_get_instance_status(vm_id, verbose=False):
    """
    Query VM status
    Returns: "Stopping" | "Stopped" | "Starting" | "Running"
    """
    status = (
        shell_command(
            f"aliyun ecs DescribeInstances --InstanceIds '[\"{vm_id}\"]'"
            + " | jq -r .Instances.Instance[0].Status",
            verbose=verbose,
            exit_on_error=True,
            capture_output=True,
        )
        .stdout.decode()
        .strip()
    )
    return status
