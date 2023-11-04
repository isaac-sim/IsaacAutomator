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
Utils for Azure
"""

import click

from src.python.utils import colorize_info, read_meta, shell_command


def azure_login(verbose=False):
    """
    Log into Azure
    """

    # detect if we need to re-login
    logged_in = (
        '"Enabled"'
        == shell_command(
            "az account show --query state",
            verbose=verbose,
            exit_on_error=False,
            capture_output=True,
        )
        .stdout.decode()
        .strip()
    )

    if not logged_in:
        click.echo(colorize_info("* Logging into Azure..."))
        shell_command("az login --use-device-code", verbose=verbose)


def azure_stop_instance(vm_id, verbose=False):
    shell_command(
        f"az vm deallocate --ids {vm_id}",
        verbose=verbose,
        exit_on_error=True,
        capture_output=False,
    )


def azure_start_instance(vm_id, verbose=False):
    shell_command(
        f"az vm start --ids {vm_id}",
        verbose=verbose,
        exit_on_error=True,
        capture_output=False,
    )
