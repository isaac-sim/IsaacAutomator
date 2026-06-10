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
import os
import shlex
import sys
from pathlib import Path

import click

from src.python.config import c as config
from src.python.utils import (
    colorize_error,
    colorize_info,
    shell_command,
)


def _aws_env_credentials_set():
    """True when AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY are both in env."""
    return bool(
        os.environ.get("AWS_ACCESS_KEY_ID")
        and os.environ.get("AWS_SECRET_ACCESS_KEY")
    )

# AWS credentials are stored in state/.aws/ which is symlinked to /root/.aws/
# in the Docker container. This makes them compatible with the AWS CLI
# and terraform's default credential chain, similar to how Azure and GCP
# credentials are handled via state/.azure/ and state/.gcp/.

AWS_STATE_DIR = f"{config['state_dir']}/.aws"


def _aws_profile():
    """AWS CLI profile used by the default credential-chain SSO flow."""
    return os.environ.get("AWS_PROFILE") or "default"


def _aws_cli_get(key, verbose=False, profile=None):
    """
    Read a value from the AWS CLI configuration.
    Returns the value or empty string if not set.
    """
    profile_arg = f" --profile {shlex.quote(profile)}" if profile else ""
    res = shell_command(
        f"aws configure get {key}{profile_arg}",
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
    Load AWS credentials, preferring env vars over the AWS CLI configuration.
    Returns dict with aws_access_key_id, aws_secret_access_key, aws_session_token, region.
    """
    if _aws_env_credentials_set():
        if verbose:
            click.echo(
                colorize_info(
                    "* Loading AWS credentials from"
                    " AWS_ACCESS_KEY_ID/AWS_SECRET_ACCESS_KEY env vars."
                )
            )
        return {
            "aws_access_key_id": os.environ.get("AWS_ACCESS_KEY_ID", ""),
            "aws_secret_access_key": os.environ.get("AWS_SECRET_ACCESS_KEY", ""),
            "aws_session_token": os.environ.get("AWS_SESSION_TOKEN", ""),
            "region": os.environ.get("AWS_DEFAULT_REGION", "")
            or _aws_cli_get("region", verbose=verbose),
        }

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


def _aws_clear_credentials(verbose=False):
    """
    Remove explicit credentials from ~/.aws/credentials so the default
    credential chain falls through to SSO.
    """
    creds_file = Path(AWS_STATE_DIR) / "credentials"
    if creds_file.exists():
        if verbose:
            click.echo(colorize_info("* Clearing stale credentials file..."))
        creds_file.unlink()


def _aws_sts_check(region="us-east-1", verbose=False):
    """
    Check if current AWS credentials are valid by calling sts get-caller-identity
    using the default credential chain.
    Returns True if credentials are valid, False otherwise.
    """
    res = shell_command(
        f"AWS_DEFAULT_REGION='{region}' aws sts get-caller-identity",
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


def _aws_sso_profile_configured(verbose=False):
    """
    True when the selected AWS CLI profile has enough SSO configuration to log in.
    Supports both current sso-session profiles and legacy inline SSO profiles.
    """
    profile = _aws_profile()
    sso_account_id = _aws_cli_get(
        "sso_account_id", verbose=verbose, profile=profile
    )
    sso_role_name = _aws_cli_get("sso_role_name", verbose=verbose, profile=profile)
    sso_session = _aws_cli_get("sso_session", verbose=verbose, profile=profile)
    sso_start_url = _aws_cli_get("sso_start_url", verbose=verbose, profile=profile)

    return bool(
        sso_account_id and sso_role_name and (sso_session or sso_start_url)
    )


def _aws_sso_login(verbose=False):
    """
    Authenticate with AWS IAM Identity Center using the standard AWS CLI SSO flow.
    """
    Path(AWS_STATE_DIR).mkdir(parents=True, exist_ok=True)
    profile = _aws_profile()

    if _aws_sso_profile_configured(verbose=verbose):
        click.echo(colorize_info(f"* Running `aws sso login --profile {profile}`..."))
        shell_command(
            f"aws sso login --profile {shlex.quote(profile)}",
            verbose=verbose,
            exit_on_error=False,
        )
        return

    click.echo(
        colorize_info(
            f"* No AWS SSO profile is configured. Running"
            f" `aws configure sso --profile {profile}`..."
        )
    )
    shell_command(
        f"aws configure sso --profile {shlex.quote(profile)}",
        verbose=verbose,
        exit_on_error=False,
    )


def aws_validate_credentials(deployment_name=None, region=None, verbose=False):
    """
    Validate AWS credentials.

    Precedence:
      1. AWS_ACCESS_KEY_ID + AWS_SECRET_ACCESS_KEY env vars (validated via STS;
         no SSO fallback and no writes to the AWS config file).
      2. SSO login flow: clears any stale exported credentials, checks the
         default credential chain, and if invalid runs the standard AWS CLI
         SSO flow (`aws sso login` for configured profiles, or
         `aws configure sso` otherwise).
         After a successful login, exports resolved credentials so Terraform
         and Packer can use them.

    Since ~/.aws is symlinked to state/.aws/, credentials persist across
    container restarts.

    If region is provided, it will be used for validation and saved to config.
    """
    click.echo(colorize_info("* Validating AWS credentials..."))

    stored_region = _aws_cli_get("region", verbose=verbose)
    effective_region = (
        region
        or os.environ.get("AWS_DEFAULT_REGION")
        or stored_region
        or "us-east-1"
    )

    if verbose:
        click.echo(colorize_info(f"* Using region: {effective_region}"))

    # Path 1: credentials supplied via env vars - skip SSO and config writes.
    if _aws_env_credentials_set():
        click.echo(
            colorize_info(
                "* Using AWS credentials from"
                " AWS_ACCESS_KEY_ID/AWS_SECRET_ACCESS_KEY env vars."
            )
        )
        if _aws_sts_check(region=effective_region, verbose=verbose):
            click.echo(colorize_info("* AWS credentials are valid!"))
            _aws_set_region(region, stored_region, effective_region, verbose)
            return
        click.echo(
            colorize_error(
                "* AWS credentials from env vars are invalid or expired."
                " Unset AWS_ACCESS_KEY_ID/AWS_SECRET_ACCESS_KEY to fall back"
                " to SSO login."
            )
        )
        sys.exit(1)

    # clear stale exported credentials so the default chain uses SSO
    _aws_clear_credentials(verbose=verbose)

    # check if we have a valid SSO session
    if _aws_sts_check(region=effective_region, verbose=verbose):
        click.echo(colorize_info("* AWS credentials are valid!"))
        _aws_export_credentials(verbose=verbose)
        _aws_set_region(region, stored_region, effective_region, verbose)
        return

    # no valid session — run SSO login
    click.echo(colorize_info("* AWS credentials are invalid, expired, or not configured."))

    while True:
        _aws_sso_login(verbose=verbose)

        click.echo(colorize_info("* Validating credentials..."))
        if _aws_sts_check(region=effective_region, verbose=verbose):
            click.echo(colorize_info("* AWS credentials are valid!"))
            _aws_export_credentials(verbose=verbose)
            _aws_set_region(region, stored_region, effective_region, verbose)
            break
        else:
            click.echo(
                colorize_error("* AWS credentials are still invalid. Please try again.")
            )


def _aws_set_region(region, stored_region, effective_region, verbose=False):
    """Save region to AWS config if needed."""
    if region and region != stored_region:
        if verbose:
            click.echo(colorize_info(f"* Updating stored region to: {region}"))
        aws_cli_set("region", region, verbose=verbose)
    elif not stored_region and effective_region:
        if verbose:
            click.echo(colorize_info(f"* Setting region to: {effective_region}"))
        aws_cli_set("region", effective_region, verbose=verbose)


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
