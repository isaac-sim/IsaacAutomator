
# Auto-Isaac

- [Usage](#usage)
  - [Pre-requisites](#pre-requisites)
  - [Deploying](#deploying)
    - [AWS](#aws)
    - [GCP](#gcp)
    - [Azure](#azure)
      - [If you have one subscription](#if-you-have-one-subscription)
      - [If You Have Multiple Subscriptions](#if-you-have-multiple-subscriptions)
  - [Connecting to Deployed Instances](#connecting-to-deployed-instances)
  - [Running Isaac Sim](#running-isaac-sim)
  - [Uploading User Files](#uploading-user-files)
  - [Downloading Results](#downloading-results)
  - [Destroying](#destroying)
- [Known Issues](#known-issues)
  - [Apple Silicon Support](#apple-silicon-support)
    - [Issue](#issue)
    - [Workaround](#workaround)

This tool automates [Isaac Sim](https://developer.nvidia.com/isaac-sim) deployment to public clouds. AWS, Azure and GCP are currently supported.

## Usage

### Pre-requisites

1. `docker` should be present on your system. Visit <https://docs.docker.com/engine/install/> for installation instructions.

2. Build the application container:

```sh
docker build -t auto-isaac .
```

3. Prepare or obtain an **NGC API Key** at <https://ngc.nvidia.com/setup/api-key>.

### Deploying

#### AWS

You will need **AWS Access Key** and **AWS Secret Key** for an existing account. You or your account administrator can obtain those in [Identity and Access Management (IAM) Section](https://console.aws.amazon.com/iamv2/home#/home) in AWS console.

Now you are ready to start a new deployment. To do so, run the following command:

```sh
# enter the container
docker run -it --rm -v `pwd`:/app auto-isaac bash
# inside container
./deploy-aws
```

Tip: Run `./deploy-aws --help` to see more options.

#### GCP

```sh
# enter the container
docker run -it --rm -v `pwd`:/app auto-isaac bash
# inside container
./deploy-gcp
```

Tip: Run `./deploy-gcp --help` to see more options.

#### Azure

##### If you have one subscription

```sh
# enter the container
docker run -it --rm -v `pwd`:/app auto-isaac bash
# inside container
./deploy-azure
```

##### If You Have Multiple Subscriptions

```sh
# enter the container
docker run -it --rm -v `pwd`:/app auto-isaac bash

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

### Running Isaac Sim

Isaac Sim will be automatically started if you choose to deploy it. To start it manually, click "Isaac Sim" icon on desktop or run the following command in a terminal:

```sh
cd ~/Desktop
# with user interface
./isaacsim.sh
# or open shell inside  isaacsim
./isaacsim-shell.sh
```

You can view available arguments with `--help` switch for the start scripts, in most cases you wouldn't need to change the defaults.

### Uploading User Files

You can upload user data from `uploads/` folder (in the project root) to the deployment by running the following command:

```sh
docker run -it --rm -v `pwd`:/app auto-isaac ./upload
```

Data will be uploaded to `/home/ubuntu/uploads` directory by default to all deployed instances. You can change this by passing `--remote-dir` argument to the command. Run `./upload --help` to see more options.

### Downloading Results

You can download user data to `results/` folder (in the project root) from deployed instances by running the following command:

```sh
docker run -it --rm -v `pwd`:/app auto-isaac ./download
```

Data will be downloaded from `/home/ubuntu/results` directory by default. You can change this by passing `--remote-dir` argument to the command. Run `./download --help` to see more options.

### Destroying

To destroy a deployment, run the following command:

```sh
docker run -it --rm -v `pwd`:/app auto-isaac ./destroy
```

You will be prompted to enter the deployment name to destroy.

*Please note that information about the deployed cloud resources is stored in `state/` directory. Do not delete this directory ever.*

## Known Issues

### Apple Silicon Support

#### Issue

Currently prebuilt NGC image is not compatible with Apple Silicon (M1/M2/etc).

#### Workaround

Build the container locally (using docker desktop or standalone docker installation) with the `--platform linux/x86_64` flag like so:

```sh
docker build -t auto-isaac --platform linux/x86_64 .
```
