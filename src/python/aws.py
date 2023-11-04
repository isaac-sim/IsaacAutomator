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
Utils for AWS
"""

from src.python.utils import read_meta, shell_command


def aws_configure_cli(
    deployment_name,
    verbose=False,
):
    """
    Configure AWS CLI for deployment
    """
    meta = read_meta(deployment_name)

    aws_access_key_id = meta["params"]["aws_access_key_id"]
    aws_secret_access_key = meta["params"]["aws_secret_access_key"]
    # region = meta["params"]["region"]

    shell_command(
        f"aws configure set aws_access_key_id '{aws_access_key_id}'",
        verbose=verbose,
        exit_on_error=True,
        capture_output=True,
    )

    shell_command(
        f"aws configure set aws_secret_access_key '{aws_secret_access_key}'",
        verbose=verbose,
        exit_on_error=True,
        capture_output=True,
    )


# def alicloud_start_vm(vm_id, verbose=False):
#     """
#     Start VM
#     """
#     shell_command(
#         f"aliyun ecs StartInstance --InstanceId '{vm_id}'",
#         verbose=verbose,
#         exit_on_error=True,
#         capture_output=True,
#     )


def aws_stop_instance(instance_id, verbose=False):
    shell_command(
        f"aws ec2 stop-instances --instance-ids '{instance_id}'",
        verbose=verbose,
        exit_on_error=True,
        capture_output=True,
    )


def aws_start_instance(instance_id, verbose=False):
    shell_command(
        f"aws ec2 start-instances --instance-ids '{instance_id}'",
        verbose=verbose,
        exit_on_error=True,
        capture_output=True,
    )


def aws_get_instance_status(instance_id, verbose=False):
    """
    Query instance status
    Returns: "stopping" | "stopped" | "pending" | "running"
    """
    status = (
        shell_command(
            f"aws ec2 describe-instances --instance-ids '{instance_id}'"
            + " | jq -r .Reservations[0].Instances[0].State.Name",
            verbose=verbose,
            exit_on_error=True,
            capture_output=True,
        )
        .stdout.decode()
        .strip()
    )
    return status


# def alicloud_get_vm_status(vm_id, verbose=False):
#     """
#     Query VM status
#     Returns: "Stopping" | "Stopped" | "Starting" | "Running"
#     """
#     status = (
#         shell_command(
#             f"aliyun ecs DescribeInstances --InstanceIds '[\"{vm_id}\"]'"
#             + " | jq -r .Instances.Instance[0].Status",
#             verbose=verbose,
#             exit_on_error=True,
#             capture_output=True,
#         )
#         .stdout.decode()
#         .strip()
#     )
#     return status
