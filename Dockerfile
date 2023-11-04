# Dockerfile for runnig and distributing the app

FROM ubuntu:20.04

ENV DEBIAN_FRONTEND=noninteractive
ENV force_color_prompt=yes

# paths for python
ENV PYTHONPATH=/app:/app/lib:/app/src:/app/py:/app/python:/app/cli:/app/utils:/app/tests

# misc
RUN apt-get update 

RUN apt-get install -qy \
    apt-utils \
    curl \
    gpg \
    lsb-release \
    openssh-client \
    wget \
    jq \
    python3-pip

RUN apt-get install -qy \
    expect \
    unzip \
    rsync

# hashicorp sources
RUN wget -O- https://apt.releases.hashicorp.com/gpg | \
    gpg --dearmor | \
    tee /usr/share/keyrings/hashicorp-archive-keyring.gpg

RUN echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] \
    https://apt.releases.hashicorp.com $(lsb_release -cs) main" | \
    tee /etc/apt/sources.list.d/hashicorp.list

# terraform
RUN apt-get update && \
    apt-get install -qy \
    terraform

# install packer
RUN apt-get install -yq packer ; exit 0

# azure command line
RUN curl -sL https://aka.ms/InstallAzureCLIDeb | bash

# store azure credentials in a persistent location
RUN ln -s /app/state/.azure /root/.azure

# pip
RUN pip install click randomname pwgen debugpy

# ansible
ENV ANSIBLE_FORCE_COLOR=true
RUN pip install ansible
RUN ansible-galaxy collection install community.docker

# ngc cli: https://docs.ngc.nvidia.com/cli/script.html
RUN cd /opt && wget https://ngc.nvidia.com/downloads/ngccli_cat_linux.zip && unzip ngccli_cat_linux.zip && rm ngccli_cat_linux.zip
RUN echo 'export PATH="$PATH:/opt/ngc-cli"' >> ~/.bashrc

# gcloud
# @see https://cloud.google.com/sdk/docs/install
RUN apt-get install -yq apt-transport-https ca-certificates gnupg
RUN echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | tee -a /etc/apt/sources.list.d/google-cloud-sdk.list
RUN curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key --keyring /usr/share/keyrings/cloud.google.gpg add -
RUN apt-get update && apt-get install -yq google-cloud-cli
RUN mkdir /root/.config && ln -s /app/state/.gcp /root/.config/gcloud

# alibaba cloud cli
# @see https://github.com/aliyun/aliyun-cli#installation
RUN /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/aliyun/aliyun-cli/HEAD/install.sh)"
RUN aliyun auto-completion

# aws cli
# @see https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html
WORKDIR /tmp
RUN curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
RUN unzip awscliv2.zip
RUN ./aws/install

# copy app code into container
COPY . /app

# customoize bash prompt
RUN echo "export PS1='\[\033[01;36m\][Isaac Sim Automator \${VERSION}]\[\033[00m\]:\w\$ '" >>  /root/.bashrc

WORKDIR /app

ENTRYPOINT [ "/bin/sh", "-c" ]

ENV VERSION="v2.0.0-rc1"
