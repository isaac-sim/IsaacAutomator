FROM "{{ isaac_image }}"

RUN apt-get update
RUN apt-get install -qy git nano

# set python and pip paths
ENV PYTHON_PATH="/isaac-sim/python.sh"
RUN echo 'alias "python"="${PYTHON_PATH}"' >> $HOME/.bashrc
RUN echo 'alias "pip"="${PYTHON_PATH} -m pip"' >> $HOME/.bashrc
RUN echo 'alias "PYTHON_PATH"="${PYTHON_PATH}"' >> $HOME/.bashrc

# if in china, add local pip mirrors
{% if in_china %}
RUN mkdir -p $HOME/.pip || true
RUN echo '[global]' >> $HOME/.pip/pip.conf
RUN echo 'index-url = http://mirrors.aliyun.com/pypi/simple' >> $HOME/.pip/pip.conf
RUN echo 'trusted-host = mirrors.aliyun.com' >> $HOME/.pip/pip.conf
{% endif %}

# install OIGE
# https://github.com/NVIDIA-Omniverse/OmniIsaacGymEnvs#installation
WORKDIR /
RUN git clone https://github.com/NVIDIA-Omniverse/OmniIsaacGymEnvs.git
RUN (cd OmniIsaacGymEnvs && git checkout {{ omni_isaac_gym_envs_git_checkpoint }})
RUN (cd OmniIsaacGymEnvs && ${PYTHON_PATH} -m pip install -e .)
WORKDIR /OmniIsaacGymEnvs/omniisaacgymenvs

# link output dir to /results
RUN mkdir /results ; ln -s /results /OmniIsaacGymEnvs/omniisaacgymenvs/runs

# customoize bash prompt
RUN echo "export PS1='\[\033[01;33m\][OmniIsaacGymEnvs]\[\033[00m\]:\w\$ '" >>  $HOME/.bashrc

# welcome message
RUN echo "echo '\\nOmniverse Isaac Gym Reinforcement Learning Environments for Isaac Sim\\nPlease see https://github.com/NVIDIA-Omniverse/OmniIsaacGymEnvs for more info.\\n'" >>  $HOME/.bashrc
