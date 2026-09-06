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
CLI Utils
"""

import json
import os
import re
import subprocess
from glob import glob
from pathlib import Path

import click

from src.python.config import c as config

# Credentials embedded in a url ("https://<token>@host/..."). The whole userinfo is
# masked: a token can sit in either field ("user:token@", "token@"), so keeping any
# part of it risks leaking the secret. The scp form "git@host:path" carries no
# credentials, so only "scheme://" urls match. Kept here (not in deploy_command) so
# shell_command can use it without importing a command module.
_URL_CREDENTIALS_RE = re.compile(r"(://)[^/@\s]+@")


def redact_url_credentials(text):
    """
    Mask credentials embedded in any url inside `text`:
      "https://user:token@host/x.git" -> "https://***@host/x.git"
    """
    if not text:
        return text
    return _URL_CREDENTIALS_RE.sub(r"\1***@", str(text))


def colorize_prompt(text):
    return click.style(text, fg="bright_cyan", italic=True)


def colorize_error(text):
    return click.style(text, fg="bright_red", italic=True)


def colorize_info(text):
    return click.style(text, fg="bright_magenta", italic=True)


def colorize_result(text):
    return click.style(text, fg="bright_green", italic=True)


def shell_command(
    command, verbose=False, cwd=None, exit_on_error=True, capture_output=False
):
    """
    Execute shell command, print it if debug is enabled
    """

    if verbose:
        # redact only the echoed copy: the command itself must keep the real
        # credentials, or the re-exec into the container would lose them
        shown = redact_url_credentials(command)
        if cwd is not None:
            click.echo(colorize_info(f"* Running `(cd {cwd} && {shown})`..."))
        else:
            click.echo(colorize_info(f"* Running `{shown}`..."))

    res = subprocess.run(
        command,
        shell=True,
        cwd=cwd,
        capture_output=capture_output,
    )

    if res.returncode == 0:
        if verbose and res.stdout is not None:
            # a child that failed to clone echoes the url it tried, credentials included
            click.echo(redact_url_credentials(res.stdout.decode()))

    elif exit_on_error:
        if res.stderr is not None:
            click.echo(
                colorize_error(
                    f"Error: {redact_url_credentials(res.stderr.decode())}"
                ),
                err=True,
            )
        exit(1)

    return res


def deployments():
    """List existing deployments by name"""
    state_dir = config["state_dir"]
    deployments = sorted(
        [
            os.path.basename(os.path.dirname(d))
            for d in glob(os.path.join(state_dir, "*/"))
        ]
    )
    return deployments


def read_meta(deployment_name: str, verbose: bool = False):
    """
    Read metadata from json file
    """

    meta_file = f"{config['state_dir']}/{deployment_name}/meta.json"

    if os.path.isfile(meta_file):
        data = json.loads(Path(meta_file).read_text())
        if verbose:
            click.echo(colorize_info(f"* Meta info loaded from '{meta_file}'"))
        return data

    raise Exception(f"Meta file '{meta_file}' not found")


def read_tf_output(deployment_name, output, verbose=False):
    """
    Read a single Terraform output value directly from the deployment's state file.

    Parses the JSON state instead of shelling out to `terraform output`. This is
    both faster and far more robust: it needs no initialized backend/.terraform and
    never executes a provider plugin - which matters on macOS, where Docker Desktop's
    bind mount cannot reliably exec the provider binaries and `terraform output -state=`
    also conflicts with a configured backend. Returns "" if the value is absent.
    """

    tfstate_file = f"{config['state_dir']}/{deployment_name}/.tfstate"
    try:
        with open(tfstate_file) as f:
            state = json.load(f)
    except (OSError, ValueError):
        return ""

    value = state.get("outputs", {}).get(output, {}).get("value")
    return "" if value is None else str(value)


def format_instance_role(instance_role):
    """
    Format instance role name for user output
    """

    formatted = {
        "isaac_workstation": "Isaac Workstation",
    }

    if instance_role in formatted:
        return formatted[instance_role]

    return instance_role


def format_cloud_name(cloud_name):
    """
    Format cloud name for user output
    """

    formatted = {
        "aws": "AWS",
        "azure": "Azure",
        "gcp": "GCP",
        "alicloud": "Alibaba Cloud",
    }

    if cloud_name in formatted:
        return formatted[cloud_name]

    return cloud_name


def gcp_login(verbose=False):
    """
    Log into GCP
    """

    # detect if we need to re-login

    click.echo(colorize_info("* Checking GCP login status..."), nl=False)
    res = shell_command(
        "gcloud auth application-default print-access-token 2>&1 > /dev/null",
        verbose=verbose,
        exit_on_error=False,
        capture_output=True,
    )

    logged_in = res.returncode == 0

    if logged_in:
        click.echo(colorize_info(" logged in!"))

    if not logged_in:
        click.echo(colorize_info(" not logged in"))
        shell_command(
            "gcloud auth application-default login --no-launch-browser --disable-quota-project --verbosity none",
            verbose=verbose,
        )


def get_my_public_ip(verbose=False):
    """
    Get the current public IP address
    """
    methods = [
        "curl -sS --max-time 2 https://api.ipify.org",
        "curl -sS --max-time 2 https://icanhazip.com",
        "curl -sS --max-time 2 https://checkip.amazonaws.com",
        # DNS-based via UDP port 53 — works even when HTTP is blocked
        "dig +short +time=2 +tries=1 myip.opendns.com @208.67.222.222",
        "dig +short +time=2 +tries=1 myip.opendns.com @208.67.220.220",
    ]
    for cmd in methods:
        res = shell_command(
            cmd, verbose=verbose, capture_output=True, exit_on_error=False
        )
        if res.returncode == 0:
            ip = res.stdout.decode().strip()
            if ip:
                if verbose:
                    click.echo(colorize_info(f"* Public IP: {ip}"))
                return ip
        if verbose:
            click.echo(
                colorize_info(f"* Failed (exit {res.returncode}), trying next...")
            )

    click.echo(
        colorize_error("Warning: Could not determine public IP address, using 0.0.0.0"),
        err=True,
    )
    return "0.0.0.0"


def subnet_from_ip(ip, mask):
    """
    Get CIDR notation from IP and mask
    """
    if "24" == mask:
        return f"{ip.rsplit('.', 1)[0]}.0/24"
    elif "16" == mask:
        return f"{ip.rsplit('.', 2)[0]}.0.0/16"
    elif "8" == mask:
        return f"{ip.rsplit('.', 3)[0]}.0.0.0/8"
    else:
        raise Exception(f"Unsupported mask: {mask}")

    return f"{ip}/{mask}"
