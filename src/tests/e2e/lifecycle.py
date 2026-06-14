#!/usr/bin/env python3

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
End-to-end AWS lifecycle driver for Isaac Automator.

Runs a full deploy -> verify -> stop -> start -> verify -> destroy cycle
against AWS, then confirms cleanup (no tagged instances/VPCs/EIPs remain
and the state dir is gone).

Spends real money. Always run with a unique --deployment-name so cleanup
queries do not collide with other deployments in the shared account.

Usage (from inside the isaac_automator container):
    python3 src/tests/e2e/lifecycle.py --deployment-name <unique-name>
"""

import shlex
import subprocess
import sys
import time
from pathlib import Path
from typing import List, Optional

import click

# verify.py lives next to this file; put its dir on sys.path so we can
# import it without making src/tests/e2e a package.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from verify import FAIL, Verifier  # noqa: E402

from src.python.config import c as config  # noqa: E402
from src.python.utils import (  # noqa: E402
    colorize_error,
    colorize_info,
    colorize_result,
    read_tf_output,
)


def run(cmd: str, *, check: bool = True, capture: bool = False, cwd: Optional[str] = None) -> subprocess.CompletedProcess:
    """Run a shell command, streaming output unless capturing."""
    click.echo(colorize_info(f"* {cmd}"))
    r = subprocess.run(
        cmd, shell=True, cwd=cwd,
        capture_output=capture, text=capture,
    )
    if check and r.returncode != 0:
        if capture and r.stderr:
            click.echo(colorize_error(r.stderr), err=True)
        raise click.ClickException(f"command failed (rc={r.returncode}): {cmd}")
    return r


def assert_in_container() -> None:
    if not Path("/.dockerenv").exists():
        raise click.ClickException(
            "lifecycle.py must run inside the isaac_automator container "
            "(it shells out to ./deploy-aws, terraform, aws, etc.). See "
            "src/tests/e2e/README.md for the docker invocation."
        )


def assert_aws_creds() -> None:
    """Fail fast if AWS creds are missing or broken."""
    r = run("aws sts get-caller-identity", capture=True, check=False)
    if r.returncode != 0:
        raise click.ClickException(
            "aws sts get-caller-identity failed - set AWS_ACCESS_KEY_ID and "
            "AWS_SECRET_ACCESS_KEY in the environment before running."
        )
    click.echo(colorize_info(f"* AWS identity: {r.stdout.strip()}"))


def run_verifier(deployment_name: str, *, label: str, debug: bool) -> None:
    click.echo(colorize_info(f"\n=== verify ({label}) ==="))
    v = Verifier(deployment_name, debug=debug)
    results = v.run_all()
    failures = [r for r in results if r.status == FAIL]
    if failures:
        raise click.ClickException(
            f"verify ({label}) failed: {[r.name for r in failures]}"
        )


def deploy(args: List[str], *, debug: bool) -> None:
    cmd = "./deploy-aws " + " ".join(shlex.quote(a) for a in args)
    if debug:
        cmd += " --debug"
    else:
        cmd += " --no-debug"
    run(cmd)


def aws_orphans(deployment_name: str, region: str) -> List[str]:
    """
    Return a list of human-readable lines describing any AWS resources
    still tagged with this deployment after destroy. Empty list means
    clean.
    """
    found: List[str] = []
    env = f"AWS_DEFAULT_REGION={shlex.quote(region)} "

    instances = run(
        env + 'aws ec2 describe-instances '
        f'--filters "Name=tag:Deployment,Values={deployment_name}" '
        '"Name=instance-state-name,Values=running,pending,stopping,stopped" '
        '--query "Reservations[].Instances[].InstanceId" --output text',
        capture=True, check=False,
    )
    if instances.stdout.strip():
        found.append(f"instances: {instances.stdout.strip()}")

    vpcs = run(
        env + 'aws ec2 describe-vpcs '
        f'--filters "Name=tag:Deployment,Values={deployment_name}" '
        '--query "Vpcs[].VpcId" --output text',
        capture=True, check=False,
    )
    if vpcs.stdout.strip():
        found.append(f"vpcs: {vpcs.stdout.strip()}")

    eips = run(
        env + 'aws ec2 describe-addresses '
        f'--filters "Name=tag:Deployment,Values={deployment_name}" '
        '--query "Addresses[].PublicIp" --output text',
        capture=True, check=False,
    )
    if eips.stdout.strip():
        found.append(f"eips: {eips.stdout.strip()}")

    return found


@click.command()
@click.option(
    "--deployment-name", required=True,
    help="Unique deployment name. Use something account-unique, e.g. 'qa-2026-05-22'.",
)
@click.option("--region", default="us-east-1", show_default=True)
@click.option("--instance-type", default="g5.2xlarge", show_default=True,
              help="Cheapest viable GPU instance for QA.")
@click.option("--isaacsim", default=None,
              help="Isaac Sim ref. Defaults to config.default_isaacsim_git_checkpoint.")
@click.option("--isaaclab", default=None,
              help="Isaac Lab ref. Defaults to config.default_isaaclab_git_checkpoint.")
@click.option("--isaaclab-arena", default="no", show_default=True,
              help="Set to a ref to include Arena. Default skips to save time.")
@click.option("--from-image/--full-deploy", default=True, show_default=True,
              help="--from-image is ~10-15 min, --full-deploy is ~45-60 min.")
@click.option("--ingress-cidrs", default="myip", show_default=True)
@click.option("--ssh-port", default=22, show_default=True, type=int)
@click.option("--ssh-user", default="ubuntu", show_default=True)
@click.option("--prefix", default="isaacautomator", show_default=True)
@click.option("--skip-stop-start", is_flag=True, default=False,
              help="Skip the stop/start IP-preservation step. Faster smoke.")
@click.option("--keep-on-failure", is_flag=True, default=False,
              help="Do NOT destroy on failure - keep resources for debugging. "
                   "REMEMBER to destroy manually with ./destroy <dn> --yes.")
@click.option("--debug/--no-debug", default=False, show_default=True)
def main(
    deployment_name: str,
    region: str,
    instance_type: str,
    isaacsim: Optional[str],
    isaaclab: Optional[str],
    isaaclab_arena: str,
    from_image: bool,
    ingress_cidrs: str,
    ssh_port: int,
    ssh_user: str,
    prefix: str,
    skip_stop_start: bool,
    keep_on_failure: bool,
    debug: bool,
):
    """Run a full AWS deploy -> verify -> stop/start -> verify -> destroy cycle."""

    assert_in_container()
    assert_aws_creds()

    isaacsim = isaacsim or config.get("default_isaacsim_git_checkpoint", "v6.0.0-dev2")
    isaaclab = isaaclab or config.get("default_isaaclab_git_checkpoint", "v3.0.0-beta")

    deploy_args = [
        "--prefix", prefix,
        "--in-china", "no",
        "--deployment-name", deployment_name,
        "--region", region,
        "--isaac-workstation-instance-type", instance_type,
        "--from-image" if from_image else "--not-from-image",
        "--ingress-cidrs", ingress_cidrs,
        "--existing", "replace",
        "--isaacsim", isaacsim,
        "--isaaclab", isaaclab,
        "--isaaclab-arena", isaaclab_arena,
        "--isaaclab-private-git", "",
        "--vnc-password", "e2etestvnc",
        "--system-user-password", "e2etestsys",
        "--ssh-port", str(ssh_port),
        "--ssh-user", ssh_user,
        "--no-upload",
    ]

    t0 = time.time()
    deployed = False
    failed = False
    debug_flag = " --debug" if debug else " --no-debug"

    try:
        click.echo(colorize_info("\n=== deploy ==="))
        deploy(deploy_args, debug=debug)
        deployed = True

        ip_before = read_tf_output(
            deployment_name, "isaac_workstation_ip", verbose=debug
        ).strip()
        click.echo(colorize_info(f"* IP after deploy: {ip_before}"))

        run_verifier(deployment_name, label="after deploy", debug=debug)

        if not skip_stop_start:
            click.echo(colorize_info("\n=== stop ==="))
            run(f"./stop {shlex.quote(deployment_name)}{debug_flag}")

            click.echo(colorize_info("\n=== start --quick ==="))
            run(f"./start {shlex.quote(deployment_name)} --quick{debug_flag}")

            ip_after = read_tf_output(
                deployment_name, "isaac_workstation_ip", verbose=debug
            ).strip()
            click.echo(colorize_info(f"* IP after start: {ip_after}"))

            if ip_before != ip_after:
                raise click.ClickException(
                    f"public IP changed across stop/start: "
                    f"{ip_before} -> {ip_after} (EIP should hold it)"
                )

            run_verifier(deployment_name, label="after stop/start", debug=debug)

    except Exception as e:
        failed = True
        click.echo(colorize_error(f"* lifecycle test failed: {e}"))

    if deployed and failed and keep_on_failure:
        click.echo(colorize_error(
            f"* --keep-on-failure set, NOT destroying. "
            f"Run `./destroy {deployment_name} --yes` manually when done."
        ))
        sys.exit(1)

    if deployed:
        click.echo(colorize_info("\n=== destroy ==="))
        destroy_ok = True
        try:
            run(f"./destroy {shlex.quote(deployment_name)} --yes{debug_flag}")
        except Exception as e:
            destroy_ok = False
            click.echo(colorize_error(f"* destroy failed: {e}"))
            click.echo(colorize_error(
                f"* clean up manually - `aws ec2 describe-instances "
                f"--filters Name=tag:Deployment,Values={deployment_name}`"
            ))

        if destroy_ok:
            click.echo(colorize_info("\n=== verify cleanup ==="))
            orphans = aws_orphans(deployment_name, region)
            if orphans:
                failed = True
                click.echo(colorize_error(f"* orphan AWS resources remain: {orphans}"))

            state_dir = Path(config["state_dir"]) / deployment_name
            if state_dir.exists():
                failed = True
                click.echo(colorize_error(
                    f"* state dir {state_dir} still exists after destroy"
                ))
        else:
            failed = True

    if failed:
        sys.exit(1)

    elapsed = int(time.time() - t0)
    click.echo(colorize_result(
        f"* OK: lifecycle complete and clean in {elapsed // 60}m {elapsed % 60}s"
    ))


if __name__ == "__main__":
    main()
