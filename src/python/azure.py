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


def azure_get_subscription_id(verbose=False):
    """
    Return the active Azure subscription id from `az account show`.
    Returns empty string if no subscription is selected.
    """
    res = shell_command(
        "az account show --query id -o tsv",
        verbose=verbose,
        exit_on_error=False,
        capture_output=True,
    )
    if res.returncode != 0:
        return ""
    return res.stdout.decode().strip()


def azure_ensure_resource_group(name, location, verbose=False):
    """
    Create the named resource group in the given location if it does not exist.
    Idempotent - succeeds when the group is already present.
    """
    res = shell_command(
        f"az group show -n {name}",
        verbose=verbose,
        exit_on_error=False,
        capture_output=True,
    )
    if res.returncode == 0:
        if verbose:
            click.echo(
                colorize_info(f"* Resource group '{name}' already exists.")
            )
        return

    click.echo(
        colorize_info(f"* Creating resource group '{name}' in '{location}'...")
    )
    shell_command(
        f"az group create -n {name} -l {location}",
        verbose=verbose,
        exit_on_error=True,
        capture_output=not verbose,
    )
