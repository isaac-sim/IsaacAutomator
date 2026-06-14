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
End-to-end verifier for a deployed Isaac Automator workstation.

Connects to a running deployment over SSH and runs smoke checks that prove
the GPU, Isaac Sim, Isaac Lab, and remote-desktop services are actually
present and healthy. Intended to run inside the isaac_automator docker
container (so terraform and ssh are available); see README.md for host
invocation.

Usage:
    python3 src/tests/e2e/verify.py <deployment-name>
"""

import shlex
import subprocess
import sys
from dataclasses import dataclass
from typing import Callable, List

import click

from src.python.config import c as config
from src.python.utils import (
    colorize_error,
    colorize_info,
    colorize_result,
    deployments,
    read_meta,
    read_tf_output,
)


PASS = "PASS"
FAIL = "FAIL"
SKIP = "SKIP"


@dataclass
class CheckResult:
    name: str
    status: str
    detail: str = ""

    def line(self) -> str:
        if self.status == PASS:
            label = colorize_result(f"[{PASS}]")
        elif self.status == SKIP:
            label = colorize_info(f"[{SKIP}]")
        else:
            label = colorize_error(f"[{FAIL}]")
        detail = f" - {self.detail}" if self.detail else ""
        return f"{label} {self.name}{detail}"


class Verifier:
    """
    Runs a fixed set of smoke checks against a deployed Isaac Automator
    workstation. The checks that exercise Isaac Sim / Isaac Lab / Isaac Lab
    Arena are conditionally skipped based on the deployment's input_params
    (e.g. --isaacsim no -> isaacsim check is skipped).
    """

    SSH_OPTS = [
        "-o", "StrictHostKeyChecking=no",
        "-o", "UserKnownHostsFile=/dev/null",
        "-o", "LogLevel=ERROR",
        "-o", "ConnectTimeout=15",
        "-o", "ServerAliveInterval=10",
        "-o", "ServerAliveCountMax=3",
    ]

    def __init__(self, deployment_name: str, debug: bool = False):
        self.deployment_name = deployment_name
        self.debug = debug

        meta = read_meta(deployment_name, verbose=debug)
        self.input_params = meta.get("input_params", {})

        self.ssh_user = self.input_params.get("ssh_user") or config["default_ssh_user"]
        self.ssh_port = int(self.input_params.get("ssh_port") or config["default_ssh_port"])
        self.key_path = f"{config['state_dir']}/{deployment_name}/key.pem"

        self.host = read_tf_output(
            deployment_name, "isaac_workstation_ip", verbose=debug
        )
        if self.host in ("", "NA"):
            raise click.ClickException(
                f"No isaac_workstation_ip found for deployment '{deployment_name}'. "
                "Is the workstation deployed and running?"
            )

    def run_remote(self, remote_cmd: str, timeout: int = 60) -> subprocess.CompletedProcess:
        """Run a single shell command on the workstation over SSH."""
        ssh_cmd = [
            "ssh",
            *self.SSH_OPTS,
            "-p", str(self.ssh_port),
            "-i", self.key_path,
            f"{self.ssh_user}@{self.host}",
            remote_cmd,
        ]
        if self.debug:
            click.echo(colorize_info(f"* ssh: {shlex.join(ssh_cmd)}"))
        return subprocess.run(
            ssh_cmd, capture_output=True, text=True, timeout=timeout
        )

    # ----- individual checks -----

    def check_ssh(self) -> CheckResult:
        try:
            r = self.run_remote("echo ok", timeout=30)
        except subprocess.TimeoutExpired:
            return CheckResult("ssh reachable", FAIL, "ssh timed out")
        if r.returncode != 0 or "ok" not in r.stdout:
            return CheckResult(
                "ssh reachable", FAIL,
                f"rc={r.returncode} stderr={r.stderr.strip()!r}",
            )
        return CheckResult("ssh reachable", PASS, f"{self.ssh_user}@{self.host}")

    def check_gpu(self) -> CheckResult:
        r = self.run_remote(
            "nvidia-smi --query-gpu=name,driver_version,memory.total "
            "--format=csv,noheader"
        )
        if r.returncode != 0:
            return CheckResult("nvidia-smi", FAIL, r.stderr.strip() or r.stdout.strip())
        line = r.stdout.strip().splitlines()
        if not line:
            return CheckResult("nvidia-smi", FAIL, "no GPU listed")
        return CheckResult("nvidia-smi", PASS, line[0])

    def check_isaacsim(self) -> CheckResult:
        requested = (self.input_params.get("isaacsim") or "").strip()
        if requested in ("", "no"):
            return CheckResult("Isaac Sim install", SKIP, "deployed with --isaacsim no")

        # Isaac Sim source dir + .build-tag matches current HEAD commit.
        # Per src/ansible/roles/isaacsim-source/tasks/install.yml:25-92.
        src_dir = f"/home/{self.ssh_user}/IsaacSim-source"
        link_dir = f"/home/{self.ssh_user}/IsaacSim"
        cmd = (
            f"test -d {src_dir} && "
            f"test -f {src_dir}/.build-tag && "
            f"cat {src_dir}/.build-tag && echo --SEP-- && "
            f"git -C {src_dir} rev-parse HEAD && echo --SEP-- && "
            f"readlink -f {link_dir}"
        )
        r = self.run_remote(cmd)
        if r.returncode != 0:
            return CheckResult(
                "Isaac Sim install", FAIL,
                f"missing IsaacSim-source/.build-tag or symlink ({r.stderr.strip()})",
            )
        parts = [p.strip() for p in r.stdout.split("--SEP--")]
        if len(parts) != 3:
            return CheckResult("Isaac Sim install", FAIL, f"unexpected output: {r.stdout!r}")
        build_tag, head, resolved = parts
        if build_tag != head:
            return CheckResult(
                "Isaac Sim install", FAIL,
                f".build-tag ({build_tag[:12]}) != HEAD ({head[:12]}) - build incomplete?",
            )
        expected_target = f"{src_dir}/_build/linux-x86_64/release"
        if resolved != expected_target:
            return CheckResult(
                "Isaac Sim install", FAIL,
                f"IsaacSim symlink -> {resolved}, expected {expected_target}",
            )
        return CheckResult(
            "Isaac Sim install", PASS,
            f"requested={requested} HEAD={head[:12]}",
        )

    def check_isaaclab(self) -> CheckResult:
        requested = (self.input_params.get("isaaclab") or "").strip()
        if requested in ("", "no"):
            return CheckResult("Isaac Lab install", SKIP, "deployed with --isaaclab no")

        # Isaac Lab dir + .install-tag matches current HEAD commit.
        # Per src/ansible/roles/isaaclab-source/tasks/install.yml:25-90.
        lab_dir = f"/home/{self.ssh_user}/IsaacLab"
        cmd = (
            f"test -d {lab_dir} && "
            f"test -f {lab_dir}/.install-tag && "
            f"cat {lab_dir}/.install-tag && echo --SEP-- && "
            f"git -C {lab_dir} rev-parse HEAD"
        )
        r = self.run_remote(cmd)
        if r.returncode != 0:
            return CheckResult(
                "Isaac Lab install", FAIL,
                f"missing IsaacLab/.install-tag ({r.stderr.strip()})",
            )
        parts = [p.strip() for p in r.stdout.split("--SEP--")]
        if len(parts) != 2:
            return CheckResult("Isaac Lab install", FAIL, f"unexpected output: {r.stdout!r}")
        install_tag, head = parts
        if install_tag != head:
            return CheckResult(
                "Isaac Lab install", FAIL,
                f".install-tag ({install_tag[:12]}) != HEAD ({head[:12]}) - install incomplete?",
            )
        return CheckResult(
            "Isaac Lab install", PASS,
            f"requested={requested} HEAD={head[:12]}",
        )

    def check_isaaclab_arena(self) -> CheckResult:
        requested = (self.input_params.get("isaaclab_arena") or "").strip()
        if requested in ("", "no"):
            return CheckResult(
                "Isaac Lab Arena install", SKIP, "deployed with --isaaclab-arena no"
            )

        # Arena is git-checkpoint driven; no .install-tag file.
        # Per src/ansible/roles/isaaclab-arena-source/tasks/install.yml.
        arena_dir = f"/home/{self.ssh_user}/IsaacLab-Arena"
        cmd = (
            f"test -d {arena_dir} && "
            f"git -C {arena_dir} rev-parse HEAD"
        )
        r = self.run_remote(cmd)
        if r.returncode != 0:
            return CheckResult(
                "Isaac Lab Arena install", FAIL,
                f"missing IsaacLab-Arena or not a git repo ({r.stderr.strip()})",
            )
        head = r.stdout.strip()
        return CheckResult(
            "Isaac Lab Arena install", PASS,
            f"requested={requested} HEAD={head[:12]}",
        )

    def check_services(self) -> CheckResult:
        # Required services (all explicitly started by Ansible roles).
        # x11vnc-ubuntu:   src/ansible/roles/remote-desktop/tasks/vnc.yml:41
        # novnc:           src/ansible/roles/remote-desktop/tasks/novnc.yml:22
        # docker:          src/ansible/roles/system/tasks/docker.yml:57
        required = ["x11vnc-ubuntu", "novnc", "docker"]
        cmd = "systemctl is-active " + " ".join(required) + " || true"
        r = self.run_remote(cmd)
        states = r.stdout.strip().splitlines()
        if len(states) != len(required):
            return CheckResult(
                "systemd services", FAIL,
                f"got {len(states)} states for {len(required)} services: {r.stdout!r}",
            )
        inactive = [
            name for name, state in zip(required, states) if state != "active"
        ]
        if inactive:
            pairs = ", ".join(f"{n}={s}" for n, s in zip(required, states))
            return CheckResult(
                "systemd services", FAIL,
                f"inactive: {inactive} ({pairs})",
            )
        return CheckResult(
            "systemd services", PASS, ", ".join(f"{n}=active" for n in required)
        )

    def check_nxserver(self) -> CheckResult:
        # NoMachine is installed only if not already present in the image
        # (remote-desktop/tasks/main.yml). Treat as best-effort: PASS if
        # active, SKIP if the unit is unknown, FAIL only if it's a known
        # unit that's inactive/failed.
        r = self.run_remote("systemctl is-active nxserver 2>&1 || true")
        state = r.stdout.strip().splitlines()[0] if r.stdout.strip() else ""
        if state == "active":
            return CheckResult("nxserver (NoMachine)", PASS, "active")
        if state in ("unknown", "inactive") and "could not be found" not in r.stdout.lower():
            # unit known but not active
            return CheckResult(
                "nxserver (NoMachine)", FAIL, f"state={state}"
            )
        return CheckResult(
            "nxserver (NoMachine)", SKIP, f"unit not present (state={state!r})"
        )

    # ----- driver -----

    def all_checks(self) -> List[Callable[[], CheckResult]]:
        return [
            self.check_ssh,
            self.check_gpu,
            self.check_services,
            self.check_nxserver,
            self.check_isaacsim,
            self.check_isaaclab,
            self.check_isaaclab_arena,
        ]

    def run_all(self) -> List[CheckResult]:
        results: List[CheckResult] = []
        click.echo(colorize_info(
            f"* Verifying deployment '{self.deployment_name}' at {self.host}"
        ))
        for check in self.all_checks():
            try:
                res = check()
            except subprocess.TimeoutExpired as e:
                res = CheckResult(check.__name__, FAIL, f"timeout: {e}")
            except Exception as e:
                res = CheckResult(check.__name__, FAIL, f"exception: {e}")
            click.echo(res.line())
            results.append(res)
            # If ssh itself failed, every subsequent remote check will fail
            # and the output is just noise. Short-circuit.
            if check is self.check_ssh and res.status == FAIL:
                click.echo(colorize_error(
                    "* ssh failed - skipping remaining remote checks"
                ))
                break
        return results


def deployments_callback(ctx, param, value):
    if value not in deployments():
        raise click.BadParameter(
            f"Invalid deployment name '{value}'. Must be one of: "
            f"[{', '.join(deployments())}]."
        )
    return value


@click.command()
@click.argument("deployment_name", required=True, callback=deployments_callback)
@click.option("--debug/--no-debug", default=False, show_default=True)
def main(deployment_name: str, debug: bool):
    """Verify a deployed Isaac Automator workstation."""
    v = Verifier(deployment_name, debug=debug)
    results = v.run_all()

    n_pass = sum(1 for r in results if r.status == PASS)
    n_fail = sum(1 for r in results if r.status == FAIL)
    n_skip = sum(1 for r in results if r.status == SKIP)

    summary = f"{n_pass} passed, {n_fail} failed, {n_skip} skipped"
    if n_fail == 0:
        click.echo(colorize_result(f"* OK: {summary}"))
        sys.exit(0)
    else:
        click.echo(colorize_error(f"* FAIL: {summary}"))
        sys.exit(1)


if __name__ == "__main__":
    main()
