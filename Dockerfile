# Dockerfile for runnig and distributing the app

FROM ubuntu:22.04

ARG WITH_PACKER=1

ENV DEBIAN_FRONTEND=noninteractive
ENV force_color_prompt=yes

# paths for python
ENV PYTHONPATH=/app:/app/lib:/app/src:/app/py:/app/python:/app/cli:/app/utils:/app/tests

# misc
RUN apt-get update && apt-get install -qy \
    openssh-client \
    lsb-release \
    python3-pip \
    apt-utils \
    expect \
    unzip \
    rsync \
    curl \
    nano \
    wget \
    gpg \
    jq

# hashicorp sources
RUN apt-get install -yq software-properties-common

RUN wget -O- https://apt.releases.hashicorp.com/gpg | \
    gpg --dearmor | \
    tee /usr/share/keyrings/hashicorp-archive-keyring.gpg > /dev/null

RUN echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(grep -oP '(?<=UBUNTU_CODENAME=).*' /etc/os-release || lsb_release -cs) main" | tee /etc/apt/sources.list.d/hashicorp.list

RUN apt-get update

# terraform
RUN apt-get install -qy terraform

# install packer & plugins
COPY . /tmp/app
RUN if [ "$WITH_PACKER" = "1" ]; then \
    apt-get install -yq packer; \
    (cd /tmp/app/src/packer/azure/isaac && packer init .) \
    && (cd /tmp/app/src/packer/aws/isaac && packer init .) \
    else \
    echo "Skipping Packer installation"; \
    fi

# azure command line
RUN curl -sL https://aka.ms/InstallAzureCLIDeb | bash
# store azure credentials in a persistent location
RUN ln -s /app/state/.azure /root/.azure

# create dir if it doesnt exist
RUN echo "mkdir -p /app/state/.azure" >> /root/.bashrc

# pip
RUN pip install click randomname pwgen debugpy

# ansible
ENV ANSIBLE_FORCE_COLOR=true
# for some reason, the ansible.cfg file is not being picked up on Windows
ENV ANSIBLE_CONFIG="/app/src/ansible/ansible.cfg"
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
RUN mkdir -p /root/.config && ln -s /app/state/.gcp /root/.config/gcloud
RUN echo "mkdir -p /app/state/.gcp" >> /root/.bashrc

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
RUN echo "export PS1='\[\033[01;36m\][Isaac Automator \${VERSION}]\[\033[00m\]:\w\$ '" >>  /root/.bashrc
# set NGC_CLI_API_KEY to contents of NGC_API_KEY var (if it exists:
RUN echo "if [ -n \"\$NGC_API_KEY\" ]; then export NGC_CLI_API_KEY=\"\$NGC_API_KEY\"; fi" >> /root/.bashrc

WORKDIR /app

ENTRYPOINT [ "/bin/sh", "-c" ]

ENV VERSION="v3.12.0"
