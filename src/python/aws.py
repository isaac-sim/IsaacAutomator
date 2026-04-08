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
Utils for AWS
"""

import json
from pathlib import Path

import click

from src.python.config import c as config
from src.python.utils import (
    colorize_error,
    colorize_info,
    shell_command,
)

# AWS credentials are stored in state/.aws/ which is symlinked to /root/.aws/
# in the Docker container. This makes them compatible with the AWS CLI
# and terraform's default credential chain, similar to how Azure and GCP
# credentials are handled via state/.azure/ and state/.gcp/.

AWS_STATE_DIR = f"{config['state_dir']}/.aws"


def _aws_cli_get(key, verbose=False):
    """
    Read a value from the AWS CLI configuration.
    Returns the value or empty string if not set.
    """
    res = shell_command(
        f"aws configure get {key}",
        verbose=verbose,
        exit_on_error=False,
        capture_output=True,
    )
    if res.returncode == 0:
        return res.stdout.decode().strip()
    return ""


def aws_cli_set(key, value, verbose=False):
    """
    Set a value in the AWS CLI configuration.
    """
    shell_command(
        f"aws configure set {key} '{value}'",
        verbose=verbose,
        exit_on_error=True,
        capture_output=True,
    )


def aws_load_credentials(verbose=False):
    """
    Load AWS credentials from the AWS CLI configuration.
    Returns dict with aws_access_key_id, aws_secret_access_key, aws_session_token, region.
    """
    if verbose:
        click.echo(colorize_info(f"* Loading AWS credentials from {AWS_STATE_DIR}/"))

    creds = {
        "aws_access_key_id": _aws_cli_get("aws_access_key_id", verbose=verbose),
        "aws_secret_access_key": _aws_cli_get("aws_secret_access_key", verbose=verbose),
        "aws_session_token": _aws_cli_get("aws_session_token", verbose=verbose),
        "region": _aws_cli_get("region", verbose=verbose),
    }

    if verbose:
        has_key = bool(creds.get("aws_access_key_id"))
        has_secret = bool(creds.get("aws_secret_access_key"))
        has_token = bool(creds.get("aws_session_token"))
        click.echo(
            colorize_info(
                f"* AWS credentials loaded: key={'yes' if has_key else 'no'},"
                f" secret={'yes' if has_secret else 'no'},"
                f" token={'yes' if has_token else 'no'},"
                f" region={creds.get('region') or '(not set)'}"
            )
        )

    return creds


def _aws_sts_check(
    aws_access_key_id=None,
    aws_secret_access_key=None,
    aws_session_token="",
    region="us-east-1",
    verbose=False,
):
    """
    Check AWS credentials by calling sts get-caller-identity.
    If explicit credentials are provided, they are passed via env vars.
    Otherwise, relies on the default AWS credential chain (supports SSO login).
    Returns True if credentials are valid, False otherwise.
    """
    if aws_access_key_id and aws_secret_access_key:
        env_override = (
            f"AWS_ACCESS_KEY_ID='{aws_access_key_id}'"
            f" AWS_SECRET_ACCESS_KEY='{aws_secret_access_key}'"
            f" AWS_DEFAULT_REGION='{region}'"
        )
        if aws_session_token:
            env_override += f" AWS_SESSION_TOKEN='{aws_session_token}'"
        cmd = f"{env_override} aws sts get-caller-identity"
    else:
        cmd = f"AWS_DEFAULT_REGION='{region}' aws sts get-caller-identity"

    res = shell_command(
        cmd,
        verbose=verbose,
        exit_on_error=False,
        capture_output=True,
    )

    if verbose:
        if res.returncode == 0:
            click.echo(colorize_info(f"* STS response: {res.stdout.decode().strip()}"))
        else:
            stderr = res.stderr.decode().strip() if res.stderr else "(no output)"
            click.echo(colorize_info(f"* STS validation failed: {stderr}"))

    return res.returncode == 0


def _aws_export_credentials(verbose=False):
    """
    Export resolved AWS credentials (e.g. from SSO login) into the AWS CLI
    config so that tools like Terraform can use them via the default
    credential chain.
    """
    res = shell_command(
        "aws configure export-credentials --format process",
        verbose=verbose,
        exit_on_error=False,
        capture_output=True,
    )

    if res.returncode != 0:
        if verbose:
            stderr = res.stderr.decode().strip() if res.stderr else "(no output)"
            click.echo(colorize_info(f"* Failed to export credentials: {stderr}"))
        return False

    try:
        exported = json.loads(res.stdout.decode())
    except (json.JSONDecodeError, UnicodeDecodeError):
        if verbose:
            click.echo(colorize_info("* Failed to parse exported credentials."))
        return False

    access_key = exported.get("AccessKeyId", "")
    secret_key = exported.get("SecretAccessKey", "")
    session_token = exported.get("SessionToken", "")

    if not access_key or not secret_key:
        if verbose:
            click.echo(colorize_info("* Exported credentials are incomplete."))
        return False

    click.echo(
        colorize_info("* Exporting SSO credentials to AWS config for Terraform...")
    )
    aws_cli_set("aws_access_key_id", access_key, verbose=verbose)
    aws_cli_set("aws_secret_access_key", secret_key, verbose=verbose)
    if session_token:
        aws_cli_set("aws_session_token", session_token, verbose=verbose)

    return True


def aws_run_configure(verbose=False):
    """
    Run `aws configure` interactively to let the user set credentials.
    """
    Path(AWS_STATE_DIR).mkdir(parents=True, exist_ok=True)
    click.echo(colorize_info("* Running `aws configure`..."))
    shell_command(
        "aws configure",
        verbose=verbose,
        exit_on_error=False,
    )


def aws_validate_credentials(deployment_name=None, region=None, verbose=False):
    """
    Validate stored AWS credentials. If invalid/expired, run `aws configure`
    to let the user re-enter them, then validate again.

    Since ~/.aws is symlinked to state/.aws/, credentials persist across
    container restarts and are automatically used by terraform and AWS CLI.

    If region is provided, it will be used for validation and saved to config.
    """
    click.echo(colorize_info("* Validating AWS credentials..."))

    current_creds = aws_load_credentials(verbose=verbose)

    # use provided region, or fall back to stored region, or default
    effective_region = region or current_creds.get("region") or "us-east-1"

    if verbose:
        click.echo(colorize_info(f"* Using region: {effective_region}"))

    # first, try the default credential chain (covers SSO login, instance profiles, etc.)
    if _aws_sts_check(region=effective_region, verbose=verbose):
        click.echo(colorize_info("* AWS credentials are valid!"))
        # if no explicit credentials are configured, export resolved
        # credentials (e.g. from SSO) so Terraform and Packer can use them
        if not current_creds.get("aws_access_key_id"):
            _aws_export_credentials(verbose=verbose)
        # ensure region is set in AWS config
        if region and region != current_creds.get("region"):
            if verbose:
                click.echo(colorize_info(f"* Updating stored region to: {region}"))
            aws_cli_set("region", region, verbose=verbose)
        elif not current_creds.get("region") and effective_region:
            if verbose:
                click.echo(colorize_info(f"* Setting region to: {effective_region}"))
            aws_cli_set("region", effective_region, verbose=verbose)
        return

    # fall back to explicit credentials from aws configure
    if current_creds.get("aws_access_key_id") and _aws_sts_check(
        current_creds["aws_access_key_id"],
        current_creds["aws_secret_access_key"],
        current_creds.get("aws_session_token", ""),
        effective_region,
        verbose=verbose,
    ):
        click.echo(colorize_info("* AWS credentials are valid!"))
        if region and region != current_creds.get("region"):
            if verbose:
                click.echo(colorize_info(f"* Updating stored region to: {region}"))
            aws_cli_set("region", region, verbose=verbose)
        elif not current_creds.get("region") and effective_region:
            if verbose:
                click.echo(colorize_info(f"* Setting region to: {effective_region}"))
            aws_cli_set("region", effective_region, verbose=verbose)
        return

    click.echo(
        colorize_info("* AWS credentials are invalid, expired, or not configured.")
    )

    while True:
        aws_run_configure(verbose=verbose)

        # reload and validate
        new_creds = aws_load_credentials(verbose=verbose)
        effective_region = region or new_creds.get("region") or effective_region

        click.echo(colorize_info("* Validating new credentials..."))

        # try default credential chain first, then explicit credentials
        if _aws_sts_check(region=effective_region, verbose=verbose):
            click.echo(colorize_info("* AWS credentials are valid!"))
            break
        elif new_creds.get("aws_access_key_id") and _aws_sts_check(
            new_creds["aws_access_key_id"],
            new_creds["aws_secret_access_key"],
            new_creds.get("aws_session_token", ""),
            effective_region,
            verbose=verbose,
        ):
            click.echo(colorize_info("* AWS credentials are valid!"))
            break
        else:
            click.echo(
                colorize_error("* AWS credentials are still invalid. Please try again.")
            )


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
