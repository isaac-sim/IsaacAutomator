FROM "{{ isaac_image }}"

# prereqs: apt packages
RUN apt-get update && apt-get install -qy \
  git wget nano ncurses-term

# prereqs: miniconda
# https://docs.conda.io/projects/miniconda/en/latest/
RUN mkdir -p ~/miniconda3
RUN wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda3/miniconda.sh
RUN bash ~/miniconda3/miniconda.sh -b -u -p ~/miniconda3
RUN rm -rf ~/miniconda3/miniconda.sh
RUN ~/miniconda3/bin/conda init bash

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
RUN ln -s ${ISAACSIM_PATH} _isaac_sim
RUN echo "alias orbit=${ORBIT_PATH}/orbit.sh" >> ${HOME}/.bashrc

RUN . ~/.bashrc && ./orbit.sh --conda
RUN . ~/.bashrc && conda activate orbit

# link output dir to /results
# RUN mkdir /results ; ln -s /results ${ORBIT_PATH}/runs

# customoize bash prompt
RUN echo "export PS1='\[\033[01;33m\][Orbit]\[\033[00m\]:\w\$ '" >>  $HOME/.bashrc

# welcome message
RUN echo "echo '\\nWelcome to Isaac Orbit!\\nPlease see https://isaac-orbit.github.io/orbit/index.html for more info.\\n'" >>  $HOME/.bashrc


