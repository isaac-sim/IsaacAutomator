# MQS Automator - Metropolis Quick Start Apps in the Cloud

This tool automates deployment of [Metropolis Quick Start](https://developer.nvidia.com/metropolis-microservices-early-access-form) applications v2.1 to the cloud.

- Multi-Target Multi-Camera App (MTMC) (https://docs.nvidia.com/mms/text/MDX_Multi_Camera_Tracking_App.html)
- Real-Time Location System App (RTLS) (https://docs.nvidia.com/mms/text/MDX_Real_Time_Location_System_App.html)
- Occupancy Analytics App (OA) (https://docs.nvidia.com/mms/text/MDX_People_Analytics_App.html)
- Occupancy Heatmap App (OH) (https://docs.nvidia.com/mms/text/MDX_People_Heatmap_App.html)

- [Installation](#installation)
  - [Prerequisites](#prerequisites)
  - [Installing Docker](#installing-docker)
  - [Building the Container](#building-the-container)
- [Usage](#usage)
  - [Tip: Running the Automator Commands](#tip-running-the-automator-commands)
  - [Deploying MQS](#deploying-mqs)
    - [AWS](#aws)
  - [Connecting to Deployed Instances](#connecting-to-deployed-instances)
  - [Running Applications](#running-applications)
    - [Install Location](#install-location)
    - [Aliases](#aliases)
  - [Pausing and Resuming](#pausing-and-resuming)
  - [Uploading Data](#uploading-data)
  - [Downloading Data](#downloading-data)
  - [Repairing](#repairing)
  - [Destroying](#destroying)


## Installation

### Prerequisites

1. Register at https://developer.nvidia.com/metropolis-microservices-early-access-form
1. Obtain an NGC API Key at https://ngc.nvidia.com/setup/api-key

### Installing Docker

`docker` should be present on your system. Visit <https://docs.docker.com/engine/install/> for installation instructions.

### Building the Container

Please enter the following command in the project root directory to build the container:

```sh
./build
```

This will build the Isaac Sim Automator container and tag it as `isa`.

## Usage

### Tip: Running the Automator Commands

There are two ways to run the automator commands:

1. First enter the automator container and then run the command inside the container:

```sh
# enter the automator container
./run
# inside container:
./somecommand
```

2. Simply prepend the command with `./run` like so:

```sh
./run ./somecommand <parameters>
```

for example:

```sh
./run ./deploy-aws
./run ./destroy my-deployment
```

### Deploying MQS

#### AWS

<details>
  <a name="#aws-permissions"></a>
  <summary>Enabling Access Permissions</summary>

  You need _AmazonEC2FullAccess_ permissions enabled for your AWS user. You can enable those in [Identity and Access Management (IAM) Section](https://console.aws.amazon.com/iamv2/home#/home) in AWS console like so:

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
  You will need _AWS Access Key_ and _AWS Secret Key_ for an existing account. You can obtain those in <a href="https://console.aws.amazon.com/iamv2/home#/home">Identity and Access Management (IAM) Section</a> in the AWS console.
</details>

If yoou have completed the above steps or already have your permissions and credentials set up, run the following command in the project root directory:

```sh
# enter the automator container
./run
# inside container:
./deploy-aws
```

Tip: Run `./deploy-aws --help` to see more options.

### Connecting to Deployed Instances

Deployed Isaac Sim instances can be accessed via:

- SSH
- noVNC (browser-based VNC client)
- NoMachine (remote desktop client)

Look for the connection instructions at the end of the deploymnt command output. Additionally, this info is saved in `state/<deployment-name>/info.txt` file.

You can view available arguments with `--help` switch for the start scripts, in most cases you wouldn't need to change the defaults.

Tip: You can use `./connect <deployment-name>` helper command to connect to the deployed instance via ssh.

### Running Applications

To use installed applications, connect to the deployed instance using noVNC or NoMachine. You can find the connection instructions at the end of the deployment command output. Additionally, this info is saved in `state/<deployment-name>/info.txt` file.

#### Install Location

Applications are installed in `/opt/metropolis-apps/standalone-deployment` directory. You can navigate to this directory and run the applications according to the instructions in the Metropolis Quick Start documentation (https://developer.nvidia.com/metropolis-microservices-members-only).

#### Aliases

The following aliases are available for starting and stopping the applications:

```sh
# Multi-Target Multi-Camera App (MTMC):
start-mtmc-e2e
start-mtmc-playback
stop-mtmc-e2e
stop-mtmc-playback

# Real-Time Location System App (RTLS):
start-rtls-e2e
start-rtls-playback
stop-rtls-e2e
stop-rtls-playback

# Occupancy Analytics App (OA):
start-oa-e2e
start-oa-playback
stop-oa-e2e
stop-oa-playback

# Occupancy Heatmap App (OH):
start-oh
stop-oh
```

### Pausing and Resuming

You can stop and re-start instances to save on cloud costs. To do so, run the following commands:

```sh
# enter the automator container
./run
# inside container:
./stop <deployment-name>
./start <deployment-name>
```

### Uploading Data

You can upload user data from `uploads/` folder (in the project root) to the deployment by running the following command:

```sh
# enter the automator container
./run
# inside container:
./upload <deployment-name>
```

Data will be uploaded to `/home/ubuntu/uploads` directory by default to all deployed instances. You can change this by passing `--remote-dir` argument to the command. Run `./upload --help` to see more options.

### Downloading Data

You can download user data to `results/` folder (in the project root) from deployed instances by running the following command:

```sh
# enter the automator container
./run
# inside container:
./download <deployment-name>
```

Data will be downloaded from `/home/ubuntu/results` directory by default. You can change this by passing `--remote-dir` argument to the command. Run `./download --help` to see more options.

### Repairing

If for some reason the deployment cloud resouces or software configuration get corrupted, you can attempt to repair the deployment by running the following command:

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
# enter the automator container
./run
# inside container:
./destroy <deployment-name>
```

You will be prompted to enter the deployment name to destroy.

*Please note that information about the deployed cloud resources is stored in `state/` directory. Do not delete this directory ever.*
