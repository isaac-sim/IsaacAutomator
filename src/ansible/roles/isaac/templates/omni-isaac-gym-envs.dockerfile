FROM "{{ isaac_image }}"

RUN apt-get update
RUN apt-get install -qy git nano

# set python and pip paths
ENV PYTHON_PATH="/isaac-sim/python.sh"
RUN echo 'alias "python"="${PYTHON_PATH}"' >> /root/.bashrc
RUN echo 'alias "pip"="${PYTHON_PATH} -m pip"' >> /root/.bashrc
RUN echo 'alias "PYTHON_PATH"="${PYTHON_PATH}"' >> /root/.bashrc

WORKDIR /
RUN git clone https://github.com/NVIDIA-Omniverse/OmniIsaacGymEnvs.git
RUN (cd OmniIsaacGymEnvs && ${PYTHON_PATH} -m pip install -e .)
WORKDIR /OmniIsaacGymEnvs/omniisaacgymenvs

# link output dir to /results
RUN mkidr /results ; ln -s /results /OmniIsaacGymEnvs/omniisaacgymenvs/runs

# customoize bash prompt
RUN echo "export PS1='\[\033[01;33m\][OmniIsaacGymEnvs]\[\033[00m\]:\w\$ '" >>  /root/.bashrc

# welcome message
RUN echo "echo '\\nOmniverse Isaac Gym Reinforcement Learning Environments for Isaac Sim\\nPlease see https://github.com/NVIDIA-Omniverse/OmniIsaacGymEnvs for more info.\\n'" >>  /root/.bashrc
