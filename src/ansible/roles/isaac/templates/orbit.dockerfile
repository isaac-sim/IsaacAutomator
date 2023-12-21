FROM "{{ isaac_image }}"

# prereqs: apt packages
RUN apt-get update && apt-get install -qy \
  git nano cmake build-essential ncurses-term

# if in china, add local pip mirrors
{% if in_china %}
RUN mkdir -p $HOME/.pip || true
RUN echo '[global]' >> $HOME/.pip/pip.conf
RUN echo 'index-url = http://mirrors.aliyun.com/pypi/simple' >> $HOME/.pip/pip.conf
RUN echo 'trusted-host = mirrors.aliyun.com' >> $HOME/.pip/pip.conf
{% endif %}

# install Orbit
# https://isaac-orbit.github.io/orbit/source/setup/installation.html#installing-orbit

ARG ORBIT_PATH="/orbit"
WORKDIR ${ORBIT_PATH}

ENV ISAACSIM_PATH="/isaac-sim"
ENV ISAACSIM_PYTHON_EXE="${ISAACSIM_PATH}/python.sh"

RUN git clone https://github.com/NVIDIA-Omniverse/Orbit.git .
RUN git checkout {{ orbit_git_checkpoint }}
RUN ln -s ${ISAACSIM_PATH} _isaac_sim
RUN echo "alias orbit=${ORBIT_PATH}/orbit.sh" >> ${HOME}/.bashrc

RUN ./orbit.sh --install
RUN ./orbit.sh --extra

RUN ${ISAACSIM_PYTHON_EXE} -c "import omni.isaac.orbit; print('Orbit configuration is now complete.')"

# link mapped folders to orbit path
RUN mkdir /results ; ln -s /results ${ORBIT_PATH}/
RUN mkdir /uploads ; ln -s /uploads ${ORBIT_PATH}/
RUN mkdir /workspace ; ln -s /workspace ${ORBIT_PATH}/

# customoize bash prompt
RUN echo "export PS1='\[\033[01;33m\][Orbit]\[\033[00m\]:\w\$ '" >>  $HOME/.bashrc

# welcome message
RUN echo "echo '\\nWelcome to Isaac Orbit!\\nPlease see https://isaac-orbit.github.io/orbit/index.html for more info.\\n'" >>  $HOME/.bashrc


