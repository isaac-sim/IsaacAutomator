FROM "{{ isaac_image }}"

RUN apt-get update
RUN apt-get install -qy git nano

# set ISAACSIM_PATH
ENV ISAACSIM_PATH="/isaac-sim"

# set ISAACSIM_PYTHON_EXE
ENV ISAACSIM_PYTHON_EXE="${ISAACSIM_PATH}/python.sh"
RUN echo 'alias "python"="${ISAACSIM_PYTHON_EXE}"' >> $HOME/.bashrc
RUN echo 'alias "pip"="${ISAACSIM_PYTHON_EXE} -m pip"' >> $HOME/.bashrc

# if in china, add local pip mirrors
{% if in_china %}
RUN mkdir -p $HOME/.pip || true
RUN echo '[global]' >> $HOME/.pip/pip.conf
RUN echo 'index-url = http://mirrors.aliyun.com/pypi/simple' >> $HOME/.pip/pip.conf
RUN echo 'trusted-host = mirrors.aliyun.com' >> $HOME/.pip/pip.conf
{% endif %}

# install Orbit
# https://isaac-orbit.github.io/orbit/source/setup/installation.html#installing-orbit
WORKDIR /
RUN git clone https://github.com/NVIDIA-Omniverse/Orbit.git

# link output dir to /results
# RUN mkdir /results ; ln -s /results /Orbit/runs

# customoize bash prompt
RUN echo "export PS1='\[\033[01;33m\][Orbit]\[\033[00m\]:\w\$ '" >>  $HOME/.bashrc

# welcome message
RUN echo "echo '\\nWelcome to Isaac Orbit!\\nPlease see https://isaac-orbit.github.io/orbit/index.html for more info.\\n'" >>  $HOME/.bashrc
