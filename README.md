![Isaac Automator](src/banner.png)

# Isaac Automator (v4)

Isaac Automator allows quick deployment of Isaac Sim and Isaac Lab to public clouds (AWS, GCP, Azure, and Alibaba Cloud are currently supported).

The result is a fully configured deployed Isaac Workstation — a remote desktop cloud VM that you can use to develop and test robotic applications within minutes and on a budget. Isaac Automator supports a variety of GPU instances and stop/start functionality to save on cloud costs and provides tools to aid your workflow (uploading and downloading data, autorun, deployment management, etc.).

- [TLDR ;)](#tldr-)
- [Installation](#installation)
  - [Installing Docker](#installing-docker)
  - [Building the Container](#building-the-container)
    - [Linux/macOS](#linuxmacos)
    - [Windows](#windows)
- [Usage](#usage)
  - [Running Isaac Automator](#running-isaac-automator)
    - [Linux/macOS](#linuxmacos-1)
    - [Windows](#windows-1)
  - [Deploying an Isaac Workstation](#deploying-an-isaac-workstation)
    - [AWS](#aws)
    - [GCP](#gcp)
    - [Azure](#azure)
    - [Alibaba Cloud](#alibaba-cloud)
    - [Common Deploy Options](#common-deploy-options)
    - [Complete Options Reference](#complete-options-reference)
  - [Credential Management](#credential-management)
  - [Connecting to Deployed Isaac Workstation](#connecting-to-deployed-isaac-workstation)
  - [Running Applications](#running-applications)
    - [Isaac Sim](#isaac-sim)
    - [Isaac Lab](#isaac-lab)
  - [Autorun Script](#autorun-script)
  - [Standard Folders](#standard-folders)
  - [Pausing and Resuming](#pausing-and-resuming)
  - [Uploading Data](#uploading-data)
  - [Downloading Data](#downloading-data)
  - [Repairing](#repairing)
  - [Destroying](#destroying)
  - [Speeding Up Deployment with Pre-Built Images](#speeding-up-deployment-with-pre-built-images)
- [Tips](#tips)
  - [Persisting Modifications to the deployed Isaac Workstation](#persisting-modifications-to-the-deployed-isaac-workstation)

## TLDR ;)

```sh
./build                       # build the Isaac Automator container (one-time)
./run                         # enter the container
./deploy-aws                  # deploy an Isaac Workstation (follow the prompts)
./novnc <deployment-name>     # open the remote desktop in your browser
./destroy <deployment-name>   # tear down the deployment when done
./image-aws                   # build a pre-built AWS AMI with Packer
```

Replace `deploy-aws` with `deploy-gcp`, `deploy-azure`, or `deploy-alicloud` for other clouds. See sections below for details.

## Installation

### Installing Docker

Docker should be installed on your system. Visit <https://docs.docker.com/engine/install/> for installation instructions.

### Building the Container

Please enter the following command in the project root directory to build the container:

#### Linux/macOS

```sh
./build
```

#### Windows

```sh
docker build --platform linux/x86_64 -t isaac_automator .
```

This will build the Isaac Automator container and tag it as `isaac_automator`.

## Usage

### Running Isaac Automator

#### Linux/macOS

On Linux and macOS there are two ways to run Isaac Automator commands:

1. First enter the Isaac Automator container and then run the command inside the container:

```sh
# enter Isaac Automator container
./run
# inside container:
./somecommand
```

2. Simply prepend the command with `./run`, like so:

```sh
./run ./somecommand <parameters>
```

for example:

```sh
./run ./deploy-aws
./run ./destroy my-deployment
```

#### Windows

On Windows, you can run Isaac Automator commands by entering the container first and then running the command inside the container, like so:

(enter Isaac Automator container)

```sh
docker run --platform linux/x86_64 -it --rm -v .:/app isaac_automator bash
```

(run the command inside the container)

```sh
./somecommand
```

### Deploying an Isaac Workstation

#### AWS

<details>
  <a name="#aws-permissions"></a>
  <summary>Enabling Access Permissions</summary>

  You need _AmazonEC2FullAccess_ permissions enabled for your AWS user. You can enable those in the [Identity and Access Management (IAM) section](https://console.aws.amazon.com/iamv2/home#/home) of the AWS console, as follows:

  1. Go to <https://console.aws.amazon.com/iamv2/home#/home>
  2. Click "Access Management" \> "Users" in the left menu
  3. Search for your user name
  4. Under "Permissions" tab click "Add permissions"
  5. Choose "Attach existing policies directly"
  6. Search for _AmazonEC2FullAccess_, check the box next to it, click "Next"
  7. Click "Add permissions"
</details>

<details>
  <a name="#aws-access-creds"></a>
  <summary>Getting Access Credentials</summary>
  You will need an _AWS Access Key_ and _AWS Secret Key_ for an existing account. You can obtain those in the [Identity and Access Management (IAM) section](https://console.aws.amazon.com/iamv2/home#/home) of the AWS console.
</details>

If you have completed the above steps or already have your permissions and credentials set up, run the following command in the project root directory:

```sh
# enter Isaac Automator container
./run
# inside container:
./deploy-aws
```

On the first run (or when credentials expire), you will be prompted to enter your AWS credentials (via `aws configure`). The credentials are stored in `state/.aws/` and persist across Isaac Automator restarts.

Tip: Run `./deploy-aws --help` to see more options.

#### GCP

<details>
  <summary>Setting Up GCP Access</summary>

  You will be prompted to log in with your Google account (`gcloud auth login`) during the first deployment. The credentials are stored in `state/.gcp/` and persist across container restarts.

  Make sure you have a GCP project with Compute Engine API enabled and sufficient GPU quota in the target zone.
</details>

```sh
# enter Isaac Automator container
./run
# inside container:
./deploy-gcp
```

Tip: Run `./deploy-gcp --help` to see more options.

#### Azure

<details>
  <summary>Setting Up Azure Access</summary>

  You will be prompted to log in with your Azure account (`az login`) during the first deployment. The credentials are stored in `state/.azure/` and persist across container restarts.

  If you have multiple subscriptions, select the desired one before deploying:

  ```sh
  # inside container:
  az login
  az account show --output table       # list subscriptions
  az account set --subscription "<subscription_name>"
  ./deploy-azure --no-login
  ```
</details>

If you have a single subscription:

```sh
# enter Isaac Automator container
./run
# inside container:
./deploy-azure
```

Tip: Run `./deploy-azure --help` to see more options.

#### Alibaba Cloud

<details>
  <a name="#alicloud-access-creds"></a>
  <summary>Getting Access Credentials</summary>
  You will need an _Access Key_ and _Secret Key_ for an existing Alibaba Cloud account. You can obtain those in the [AccessKey Management](https://usercenter.console.aliyun.com/#/manage/ak) section of the Alibaba Cloud console.
</details>

Once you have prepared the access credentials, run the following command in the project root directory:

```sh
# enter Isaac Automator container
./run
# inside container:
./deploy-alicloud
```

Tip: Run `./deploy-alicloud --help` to see more options.

GPU-accelerated instances with NVIDIA A100, A10, and T4 GPUs are supported. You can find the complete list of instance types, availability, and pricing at <https://www.alibabacloud.com/help/en/ecs/user-guide/gpu-accelerated-compute-optimized-and-vgpu-accelerated-instance-families-1>. Please note that vGPU instances are not supported.

#### Common Deploy Options

All `deploy-*` commands accept the deployment name as an optional positional argument:

```sh
./deploy-aws my-deployment
# equivalent to:
./deploy-aws --deployment-name my-deployment
```

Run `./deploy-<cloud> --help` to see the full list of options. Key options include:

- `--existing` — What to do if a deployment with the same name already exists. Choices:
  - `ask` (default) — prompt interactively
  - `repair` — fix a broken deployment without changing parameters
  - `modify` — update parameters and attempt to update existing cloud resources
  - `replace` — delete old cloud resources first, then redeploy
  - `run_ansible` — re-run software configuration (Ansible) only
- `--instance-type` — Cloud VM instance type (each cloud has its own supported list and default).
- `--isaacsim` / `--isaaclab` — Git ref for Isaac Sim / Isaac Lab version, or `no` to skip installation.
- `--from-image` — Deploy from a pre-built VM image to speed up provisioning (not supported on GCP).
- `--in-china` — Use local mirrors for deployments in China. Choices: `auto` (default), `yes`, `no`.
- `--prefix` — Prefix for created cloud resource names (default: `isaacautomator`).
- `--ingress-cidrs` — CIDR blocks for allowed ingress traffic, comma-separated. Use `myip` for your current public IP, or `myip/16`, `myip/24` for subnets.

GCP additionally supports `--isaac-workstation-gpu-count` (choices: `1`, `2`, `4`, `8`; default: `1`) to control the number of GPUs attached to the instance:

- N1 instances: up to 4x NVIDIA T4
- G2 instances: up to 8x NVIDIA L4
- G4 instances: up to 8x NVIDIA RTX PRO 6000

<details>
<summary>deploy-aws options</summary>

#### Complete Options Reference

```
Options:
  --debug / --no-debug          Enable debug output.  [default: no-debug]
  --prefix TEXT                 Prefix for all cloud resources.  [default: isaacautomator]
  --from-image / --not-from-image
                                Deploy from pre-built image, from bare OS
                                otherwise.  [default: not-from-image]
  --in-china [auto|yes|no]      Is deployment in China? (Local mirrors will be
                                used.)  [default: auto]
  --deployment-name TEXT        Name of the deployment.  [default: <random>]
  --ingress-cidrs TEXT          CIDR blocks for ingress traffic, comma
                                separated. "myip" for your public IP.
                                [default: 0.0.0.0/0]
  --existing [ask|repair|modify|replace|run_ansible]
                                What to do if deployment already exists.
                                [default: ask]
  --isaacsim TEXT               Git ref at github.com/isaac-sim/IsaacSim, or
                                "no".  [default: v6.0.0-dev2]
  --isaaclab TEXT               Git ref at github.com/isaac-sim/IsaacLab, or
                                "no".  [default: v3.0.0-beta]
  --vnc-password TEXT           Password for VNC access.  [default: <random>]
  --system-user-password TEXT   System user password.  [default: <random>]
  --ssh-port TEXT               SSH port.  [default: 22]
  --ssh-user TEXT               OS username on the deployed instances.
                                [default: ubuntu]
  --upload / --no-upload        Upload user data from "uploads/" to cloud
                                instances.  [default: upload]
  --instance-type TEXT          Instance type (G4dn, G5, G6, G6e supported).
                                [default: g6e.2xlarge]
  --region TEXT                 AWS Region.  [default: us-east-1]

Note: AWS credentials are managed via `aws configure` and stored in
`state/.aws/`. You will be prompted to enter them on first run or when
they expire.
```

</details>

<details>
<summary>deploy-gcp options</summary>

```
Options:
  --debug / --no-debug          Enable debug output.  [default: no-debug]
  --prefix TEXT                 Prefix for all cloud resources.  [default: isaacautomator]
  --in-china [auto|yes|no]      Is deployment in China? (Local mirrors will be
                                used.)  [default: auto]
  --deployment-name TEXT        Name of the deployment.  [default: <random>]
  --zone TEXT                   GCP zone (see cloud.google.com/compute/docs/
                                gpus/gpu-regions-zones).
                                [default: us-central1-a]
  --project TEXT                GCP Project ID.  [default: from gcloud config]
  --ingress-cidrs TEXT          CIDR blocks for ingress traffic, comma
                                separated. "myip" for your public IP.
                                [default: 0.0.0.0/0]
  --existing [ask|repair|modify|replace|run_ansible]
                                What to do if deployment already exists.
                                [default: ask]
  --isaacsim TEXT               Git ref at github.com/isaac-sim/IsaacSim, or
                                "no".  [default: v6.0.0-dev2]
  --isaaclab TEXT               Git ref at github.com/isaac-sim/IsaacLab, or
                                "no".  [default: v3.0.0-beta]
  --vnc-password TEXT           Password for VNC access.  [default: <random>]
  --system-user-password TEXT   System user password.  [default: <random>]
  --ssh-port TEXT               SSH port.  [default: 22]
  --ssh-user TEXT               OS username on the deployed instances.
                                [default: ubuntu]
  --upload / --no-upload        Upload user data from "uploads/" to cloud
                                instances.  [default: upload]
  --instance-type [g2-standard-4|g2-standard-8|...|n1-standard-4|...|g4-standard-48|...]
                                Instance type.  [default: g2-standard-8]
  --isaac-workstation-gpu-count [1|2|4|8]
                                Number of GPUs. N1: NVIDIA T4, G2: NVIDIA L4,
                                G4: NVIDIA RTX PRO 6000.  [default: 1]

Note: --from-image is not supported on GCP.
```

</details>

<details>
<summary>deploy-azure options</summary>

```
Options:
  --debug / --no-debug          Enable debug output.  [default: no-debug]
  --prefix TEXT                 Prefix for all cloud resources.  [default: isaacautomator]
  --from-image / --not-from-image
                                Deploy from pre-built image, from bare OS
                                otherwise.  [default: not-from-image]
  --in-china [auto|yes|no]      Is deployment in China? (Local mirrors will be
                                used.)  [default: auto]
  --deployment-name TEXT        Name of the deployment.  [default: <random>]
  --region TEXT                 Azure region.  [default: westus3]
  --ingress-cidrs TEXT          CIDR blocks for ingress traffic, comma
                                separated. "myip" for your public IP.
                                [default: 0.0.0.0/0]
  --existing [ask|repair|modify|replace|run_ansible]
                                What to do if deployment already exists.
                                [default: ask]
  --isaacsim TEXT               Git ref at github.com/isaac-sim/IsaacSim, or
                                "no".  [default: v6.0.0-dev2]
  --isaaclab TEXT               Git ref at github.com/isaac-sim/IsaacLab, or
                                "no".  [default: v3.0.0-beta]
  --vnc-password TEXT           Password for VNC access.  [default: <random>]
  --system-user-password TEXT   System user password.  [default: <random>]
  --ssh-port TEXT               SSH port.  [default: 22]
  --ssh-user TEXT               OS username on the deployed instances.
                                [default: ubuntu]
  --upload / --no-upload        Upload user data from "uploads/" to cloud
                                instances.  [default: upload]
  --instance-type TEXT          VM type (T4 and A10 supported).
                                [default: Standard_NV36ads_A10_v5]
  --login / --no-login          Login into Azure before deploying.
                                [default: login]
  --resource-group TEXT         Azure resource group (created if empty).
                                [default: ""]
```

</details>

<details>
<summary>deploy-alicloud options</summary>

```
Options:
  --debug / --no-debug          Enable debug output.  [default: no-debug]
  --prefix TEXT                 Prefix for all cloud resources.  [default: isaacautomator]
  --in-china [auto|yes|no]      Is deployment in China? (Local mirrors will be
                                used.)  [default: auto]
  --deployment-name TEXT        Name of the deployment.  [default: <random>]
  --ingress-cidrs TEXT          CIDR blocks for ingress traffic, comma
                                separated. "myip" for your public IP.
                                [default: 0.0.0.0/0]
  --existing [ask|repair|modify|replace|run_ansible]
                                What to do if deployment already exists.
                                [default: ask]
  --isaacsim TEXT               Git ref at github.com/isaac-sim/IsaacSim, or
                                "no".  [default: v6.0.0-dev2]
  --isaaclab TEXT               Git ref at github.com/isaac-sim/IsaacLab, or
                                "no".  [default: v3.0.0-beta]
  --vnc-password TEXT           Password for VNC access.  [default: <random>]
  --system-user-password TEXT   System user password.  [default: <random>]
  --ssh-port TEXT               SSH port.  [default: 22]
  --ssh-user TEXT               OS username on the deployed instances.
                                [default: ubuntu]
  --upload / --no-upload        Upload user data from "uploads/" to cloud
                                instances.  [default: upload]
  --aliyun-access-key TEXT      Alibaba Cloud Access Key.
                                [default: ALIYUN_ACCESS_KEY env var]
  --aliyun-secret-key TEXT      Alibaba Cloud Secret Key.
                                [default: ALIYUN_SECRET_KEY env var]
  --region TEXT                 Alibaba Cloud Region ID.
                                [default: us-east-1]
  --instance-type TEXT          Instance type.
                                [default: ecs.gn7i-c16g1.4xlarge]

Note: --from-image is not supported on Alibaba Cloud.
```

</details>

### Credential Management

Each cloud provider's credentials are stored inside the `state/` directory so they persist across container restarts:

| Cloud         | Storage Location      | How Credentials Are Set                                                          |
| ------------- | --------------------- | -------------------------------------------------------------------------------- |
| AWS           | `state/.aws/`         | `aws configure` — prompted automatically when credentials are missing or expired |
| GCP           | `state/.gcp/`         | `gcloud auth login` — prompted during the first deployment                       |
| Azure         | `state/.azure/`       | `az login` — prompted during the first deployment                                |
| Alibaba Cloud | Environment variables | `ALIYUN_ACCESS_KEY` and `ALIYUN_SECRET_KEY` — passed from the host via `./run`   |

All commands that interact with cloud resources (`deploy-*`, `start`, `stop`, `destroy`, `repair`) validate credentials before proceeding and prompt you to re-authenticate if they are invalid or expired.

### Connecting to Deployed Isaac Workstation

Deployed Isaac Workstation can be accessed via:

- SSH
- noVNC (browser-based VNC client)
- NoMachine (remote desktop client)

Look for the connection instructions at the end of the deployment command output. Additionally, this information is saved in the `state/<deployment-name>/info.txt` file.

You can view available arguments with the `--help` switch for the start scripts. In most cases, you won't need to change the defaults.

Use `./ssh <deployment-name>` to connect to the deployed instance via SSH.

Use `./novnc <deployment-name>` to open the noVNC web client for the deployed instance.

### Running Applications

To use the installed applications, connect to the deployed Isaac Workstation using noVNC or NoMachine. You can find the connection instructions at the end of the deployment command output. Additionally, this information is saved in the `state/<deployment-name>/info.txt` file.

#### Isaac Sim

Isaac Sim is installed from source on the deployed Isaac Workstation. By default, it will automatically start when the instance is deployed. Alternatively, click the "Isaac Sim" icon on the desktop, or run the following command in a terminal on the deployed vm:

```sh
~/IsaacSim/isaac-sim.sh
```

To install a specific version of Isaac Sim, provide a valid Git reference from <https://github.com/isaac-sim/IsaacSim> as the value of the `--isaacsim` parameter to the deployment command. Use `--isaacsim no` to skip Isaac Sim installation.

#### Isaac Lab

[Isaac Lab](https://isaac-sim.github.io/IsaacLab/) is installed from source on the Isaac Workstation. To install a specific version of Isaac Lab, provide a valid Git reference from <https://github.com/isaac-sim/IsaacLab> as the value of the `--isaaclab` parameter to the deployment command. Use `--isaaclab no` to skip Isaac Lab installation.

To run Isaac Lab CLI, use the following command in the terminal on the deployed instance:

```sh
~/IsaacLab/isaaclab.sh [options]
```

### Autorun Script

By default, Isaac Sim will start when the cloud VM is deployed.

If you want to launch a custom application or script on startup, modify the [`uploads/autorun.sh`](uploads/autorun.sh) script (on your local machine). It will either be uploaded to the cloud VM automatically, or you can upload it manually using the `./upload` command.

Every time the cloud VM is deployed or started from a stopped state, the `autorun.sh` script will be executed.

This functionality can be useful for running batch jobs, generating data on startup, or preparing the environment for the user.

### Standard Folders

Two folders are used for exchanging data between your local machine and the deployed instance:

| Local (Isaac Automator) | Remote (Isaac Workstation) | Purpose                                                                                     |
| ----------------------- | -------------------------- | ------------------------------------------------------------------------------------------- |
| `uploads/`              | `~/uploads`                | Data you send to the instance. Synced automatically on deploy, or manually with `./upload`. |
| `results/`              | `~/results`                | Data you pull back from the instance with `./download`.                                     |

### Pausing and Resuming

You can stop and restart instances to save on cloud costs. To do so, run the following commands:

```sh
# enter Isaac Automator container
./run
# inside container:
./stop <deployment-name>
./start <deployment-name>
```

### Uploading Data

You can upload user data from the `uploads/` folder (in the project root) to the deployment by running the following command:

```sh
# enter Isaac Automator container
./run
# inside container:
./upload <deployment-name>
```

Data will be uploaded to the `/home/ubuntu/uploads` directory by default (the `ubuntu` part of the path depends on the configured `default_ssh_user`), on all deployed instances. You can change this by passing the `--remote-dir` argument to the command. By default, files deleted locally are also deleted on the remote side during sync; use `--no-delete` to keep remote files that no longer exist locally. Run `./upload --help` to see more options.

### Downloading Data

You can download user data to the `results/` folder (in the project root) from deployed instances by running the following command:

```sh
# enter Isaac Automator container
./run
# inside container:
./download <deployment-name>
```

Data will be downloaded from the `/home/ubuntu/results` directory by default (the `ubuntu` part of the path depends on the configured `default_ssh_user`). You can change this by passing the `--remote-dir` argument to the command. By default, local files not present on the remote side are deleted during sync; use `--no-delete` to keep them. Run `./download --help` to see more options.

### Repairing

If, for some reason, the deployment cloud resources or software configuration become corrupted, you can attempt to repair the deployment by running the following commands:

```sh
# run both terraform and ansible
./repair <deployment-name>
# just run terraform to try fixing the cloud resources
./repair <deployment-name> --no-ansible
# just run ansible to try fixing the software configuration
./repair <deployment-name> --no-terraform
```

### Destroying

To destroy a deployment, run the following command:

```sh
# enter Isaac Automator container
./run
# inside container:
./destroy <deployment-name>
```

_Please note that information about the deployed cloud resources is stored in the `state/` directory. Do not delete this directory._

### Speeding Up Deployment with Pre-Built Images

_At the moment, only `./image-aws` command is implemented. Versions for other clouds are in the works._

You can build pre-built AWS AMIs to speed up future deployments (using the `--from-image` flag). The `image-aws` command wraps Packer and handles AWS credential management automatically:

```sh
# enter Isaac Automator container
./run
# inside container:
./image-aws
```

The AMI name defaults to the current date and is automatically prefixed with `isaacautomator.isaacworkstation.`. When deploying with `--from-image`, Terraform picks the most recent AMI matching this prefix.

Key options:

- The image name can be passed as a positional argument: `./image-aws my-image-name`
- `--instance-type` — Instance type for the Packer build (G4dn, G5, G6, G6e supported; default: `g6e.2xlarge`)
- `--region` — AWS Region, can be entered as `us-east-1` or `US East 1` (default: `us-east-1`)
- `--existing` — What to do if an AMI with the same name already exists: `overwrite` or `fail` (default: `fail`)
- `--isaacsim` / `--isaaclab` — Git refs for the versions to bake into the image

Tip: Run `./image-aws --help` to see all options.

## Tips

### Persisting Modifications to the deployed Isaac Workstation

Isaac Workstation local data is persistent and survives `./stop`/`.start` cycles.

For changes that need to be re-applied automatically on every deployment or `./start`, modify the [`uploads/autorun.sh`](uploads/autorun.sh) script. This script runs each time the instance is deployed or started (see [Autorun Script](#autorun-script)).

For example, you can use `autorun.sh` to install additional Python packages, apply patches, or run setup scripts:

```sh
#!/bin/sh

# This script is executed when
# 1. the VM is first deployed
# 2. the VM is started after being stopped

SELF_DIR="$(dirname $0)"

# example: install additional packages into the Isaac Lab environment
pip install torch
```
