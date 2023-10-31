# Isaac Sim Automator

- [Installation](#installation)
  - [Installing Docker](#installing-docker)
  - [Obtaining NGC API Key](#obtaining-ngc-api-key)
  - [Building the Container](#building-the-container)
- [Usage](#usage)
  - [Tip: Running the Automator Commands](#tip-running-the-automator-commands)
  - [Deploying Isaac Sim](#deploying-isaac-sim)
    - [AWS](#aws)
    - [GCP](#gcp)
    - [Azure](#azure)
  - [Connecting to Deployed Instances](#connecting-to-deployed-instances)
  - [Running Applications](#running-applications)
    - [Isaac Sim](#isaac-sim)
    - [Shell in Isaac Sim Container](#shell-in-isaac-sim-container)
    - [Omniverse Isaac Gym](#omniverse-isaac-gym)
  - [Pausing and Resuming](#pausing-and-resuming)
  - [Uploading Data](#uploading-data)
  - [Downloading Data](#downloading-data)
  - [Destroying](#destroying)
- [Known Issues](#known-issues)
  - [Apple Silicon Support](#apple-silicon-support)

This tool automates [Isaac Sim](https://developer.nvidia.com/isaac-sim) deployment to public clouds. AWS, Azure and GCP are currently supported.

## Installation

### Installing Docker

`docker` should be present on your system. Visit <https://docs.docker.com/engine/install/> for installation instructions.

### Obtaining NGC API Key

**NGC API Key** allows you to download docker images from <https://ngc.nvidia.com/>. Please prepare one or obtain it at <https://ngc.nvidia.com/setup/api-key>.

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
./someconnad
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

### Deploying Isaac Sim

#### AWS

<details>
  <a href="#aws-permissions"></a>
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
  <a href="#aws-access-creds"></a>
  <summary>Getting Access Credentials</summary>
  You will need **AWS Access Key** and **AWS Secret Key** for an existing account. You can obtain those in [Identity and Access Management (IAM) Section](https://console.aws.amazon.com/iamv2/home#/home) in AWS console.
</details>

<br>

If yoou have completed the above steps or already have your permissions and credentials set up, run the following command in the project root directory:

```sh
# enter the automator container
./run
# inside container:
./deploy-aws
```

Tip: Run `./deploy-aws --help` to see more options.

#### GCP

```sh
# enter the automator container
./run
# inside container:
./deploy-gcp
```

Tip: Run `./deploy-gcp --help` to see more options.

#### Azure

If You Have Single Subscription:

```sh
# enter the automator container
./run
# inside container:
./deploy-azure
```

If You Have Multiple Subscriptions:

```sh
 # enter the automator container
./run

# inside container:
az login # login
az account show --output table # list subscriptions
az account set --subscription "<subscription_name>"
./deploy-azure --no-login
```

Tip: Run `./deploy-azure --help` to see more options.

### Connecting to Deployed Instances

Deployed Isaac Sim instances can be accessed via:

- SSH
- noVNC (browser-based VNC client)
- NoMachine (remote desktop client)

Look for the connection instructions at the end of the deploymnt command output. Additionally, this info is saved in `state/<deployment-name>/info.txt` file.

You can view available arguments with `--help` switch for the start scripts, in most cases you wouldn't need to change the defaults.

### Running Applications

To use installed applications, connect to the deployed instance using noVNC or NoMachine. You can find the connection instructions at the end of the deployment command output. Additionally, this info is saved in `state/<deployment-name>/info.txt` file.

#### Isaac Sim

Isaac Sim will be automatically started when cloud VM is deployed. Alternatively you can click "Isaac Sim" icon on the desktop or run the following command in the terminal on the deployed instance or launch it from the terminal as follows:

```sh
~/Desktop/isaacsim.sh
```

#### Shell in Isaac Sim Container

To get a shell inside Isaac Sim container, click "Isaac Sim Shell" icon on the desktop. Alternatively you can run the following command in the terminal on the deployed instance:

```sh
~/Desktop/isaacsim-shell.sh
```

#### Omniverse Isaac Gym

[Omniverse Isaac Gym Reinforcement Learning Environments for Isaac Sim](https://github.com/NVIDIA-Omniverse/OmniIsaacGymEnvs) ("Omniverse Isaac Gym") is pre-installed on the deployed Isaac instances.

To run Omniverse Isaac Gym click "Omni Isaac Gym" icon on the desktop or run the following command in the terminal:

```sh
~/Desktop/omni-isaac-gym-envs.sh
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

Currently, stop-start is only supported for Azure deployments, other clouds will be added soon.

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

## Known Issues

### Apple Silicon Support

Issue:

Some packages in the application docker container are not compatible with ARM architecture of Apple Silicon (M1/M2/etc).

Workaround:

Build the ap container using Docker Desktop or standalone Docker installation with the `--platform linux/x86_64` flag like so:

```sh
docker build -t isa --platform linux/x86_64 .
```
