# Dockerfile for runnig and distributing the app

FROM ubuntu:20.04

ARG WITH_PACKER=false
ARG WITH_GIT=false

ENV DEBIAN_FRONTEND=noninteractive
ENV force_color_prompt=yes

# paths for python
ENV PYTHONPATH=/app:/app/lib:/app/src:/app/py:/app/python:/app/cli:/app/utils:/app/tests

# Create non-root user

ARG USERNAME=ovuser
ARG USER_UID=1000
ARG USER_GID=$USER_UID
RUN groupadd --gid $USER_GID $USERNAME \
    && useradd --uid $USER_UID --gid $USER_GID -m $USERNAME \
    && apt-get update \
    && apt-get install -y sudo \
    && echo $USERNAME ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/$USERNAME \
    && chmod 0440 /etc/sudoers.d/$USERNAME

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

# git, git completion
RUN ${WITH_GIT} && \
    apt-get install -yq git && \
    curl https://raw.githubusercontent.com/git/git/master/contrib/completion/git-completion.bash  >> ~/.bashrc \
    ; exit 0

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

# install packer plugins
RUN ${WITH_PACKER} && apt-get install -yq packer ; exit 0

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

# copy app code into container
COPY . /app

# copy .bashrc (startup commands)
RUN cat /app/utils/.bashrc >>  /root/.bashrc

WORKDIR /app

ENTRYPOINT [ "/bin/sh", "-c" ]

ENV VERSION="v1.1.0-rc1"
