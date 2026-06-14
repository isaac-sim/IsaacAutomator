# End-to-end test suite

Live-fire tests that confirm a deployed Isaac Automator workstation actually
has a working GPU, Isaac Sim, Isaac Lab, and remote-desktop services. These
tests spend real money - run with care.

Two pieces, layered:

- **`verify.py`** - reusable verifier. SSHes into a running deployment and
  runs a fixed set of smoke checks. Cheap (~30 s on a live host). Use it
  any time you want to re-confirm an existing deployment is healthy.
- **`lifecycle.py`** - full AWS lifecycle driver. Calls `./deploy-aws`,
  runs the verifier, exercises `./stop`/`./start`, re-verifies, then
  `./destroy`s and confirms cleanup. Slow and expensive (~30 min, ~$0.30
  for `--from-image`; ~60 min, ~$2 for `--full-deploy`).

## Smoke checks (what `verify.py` asserts)

1. **ssh reachable** - `ssh ubuntu@<ip> echo ok` returns 0.
2. **nvidia-smi** - `nvidia-smi --query-gpu=name,driver_version,memory.total
   --format=csv,noheader` returns a non-empty line.
3. **systemd services** - `x11vnc-ubuntu`, `novnc`, `docker` are all
   `active`. Service names come from the Ansible roles
   (`remote-desktop/tasks/{vnc,novnc}.yml`, `system/tasks/docker.yml`).
4. **nxserver (NoMachine)** - best-effort `active` check. SKIPped when the
   unit is not present (NoMachine is only installed when absent from the
   image; see `remote-desktop/tasks/main.yml`).
5. **Isaac Sim install** - `~/IsaacSim-source/.build-tag` exists and
   matches `git rev-parse HEAD` inside that dir, and `~/IsaacSim` is a
   symlink to `_build/linux-x86_64/release`. SKIPped when the deployment
   was created with `--isaacsim no`.
6. **Isaac Lab install** - `~/IsaacLab/.install-tag` exists and matches
   `git rev-parse HEAD`. SKIPped when `--isaaclab no`.
7. **Isaac Lab Arena install** - `~/IsaacLab-Arena` is a git repo. SKIPped
   when `--isaaclab-arena no`.

The verifier reads `state/<dn>/meta.json` to know what *was* requested and
skips the corresponding install checks accordingly. The build-tag /
install-tag files are written by the Ansible roles only after the build /
install completes successfully, so comparing them against the current HEAD
catches partial / failed installs.

## Running `verify.py`

Both scripts must run inside the `isaac_automator` container, where
`PYTHONPATH=/app:...`, terraform, and the `aws` CLI are all available.

Interactive shell:

```sh
./run "python3 src/tests/e2e/verify.py <deployment-name>"
```

From a non-TTY shell (CI, scripts) `./run` fails because it uses
`docker run -it`. Bypass it:

```sh
docker run --rm --network host \
  -v "$(pwd)":/app \
  -e AWS_ACCESS_KEY_ID -e AWS_SECRET_ACCESS_KEY -e AWS_DEFAULT_REGION \
  isaac_automator \
  "python3 src/tests/e2e/verify.py <deployment-name>"
```

Exit code is `0` if all non-skipped checks pass, `1` otherwise. Output
prints one `[PASS|FAIL|SKIP]` line per check plus a summary.

## Running `lifecycle.py`

```sh
docker run --rm --network host \
  -v "$(pwd)":/app \
  -e AWS_ACCESS_KEY_ID -e AWS_SECRET_ACCESS_KEY -e AWS_DEFAULT_REGION \
  isaac_automator \
  "python3 src/tests/e2e/lifecycle.py --deployment-name qa-$(date +%Y-%m-%d)"
```

Defaults are tuned for the cheapest viable QA run:

| Option              | Default       | Notes                                |
| ------------------- | ------------- | ------------------------------------ |
| `--instance-type`   | `g5.2xlarge`  | ~$1.21/hr; cheapest GPU that boots   |
| `--region`          | `us-east-1`   |                                      |
| `--from-image`      | on            | `--full-deploy` for full pipeline    |
| `--isaaclab-arena`  | `no`          | skip Arena to save time              |
| `--ingress-cidrs`   | `myip`        | `/32` of the runner's public IP      |
| `--isaacsim`        | config default| `default_isaacsim_git_checkpoint`    |
| `--isaaclab`        | config default| `default_isaaclab_git_checkpoint`    |

Useful flags:

- `--skip-stop-start` - skip the stop/start IP-preservation step. Cuts
  ~5 min off the run.
- `--keep-on-failure` - on failure, do NOT destroy. Inspect with
  `./ssh <dn>`, then destroy manually with `./destroy <dn> --yes`.
- `--full-deploy` - run a full Ansible build instead of `--from-image`.
  Use when validating the install pipeline itself.

## Cleanup discipline

`lifecycle.py` always tries to `./destroy` unless `--keep-on-failure` is
set, then queries AWS to confirm no resources with `tag:Deployment=<dn>`
remain (instances, VPCs, EIPs) and that `state/<dn>/` is gone. If you
abort the test (Ctrl-C, kill -9), clean up manually:

```sh
./destroy <dn> --yes
aws ec2 describe-instances \
  --filters "Name=tag:Deployment,Values=<dn>" \
  "Name=instance-state-name,Values=running,pending,stopping,stopped" \
  --query 'Reservations[].Instances[].InstanceId' --output text
aws ec2 describe-vpcs \
  --filters "Name=tag:Deployment,Values=<dn>" \
  --query 'Vpcs[].VpcId' --output text
aws ec2 describe-addresses \
  --filters "Name=tag:Deployment,Values=<dn>" \
  --query 'Addresses[].PublicIp' --output text
```

Pick a unique `--deployment-name` for every run - the drivesim AWS account
is shared, and tag-filtered queries will see siblings if names collide.

## What this suite does NOT do

- It does not launch Isaac Sim or Isaac Lab as running processes. The
  build-tag/install-tag matches plus a working `nvidia-smi` are taken as
  proof the install completed; this catches >90% of deploy regressions
  without spending GPU minutes on a headless launch. Extending to a
  headless `isaac-sim.sh --no-window` smoke is straightforward but adds
  ~2-3 min/run.
- It does not exercise Azure, GCP, or Alibaba Cloud. AWS only.
- It does not test upload/autorun, NoMachine GUI login, or noVNC
  browser-side rendering.
