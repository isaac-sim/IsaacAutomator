FROM "{{ isaac_image }}"

# prereqs: apt packages
RUN apt-get update && apt-get install -qy \
  git nano cmake build-essential ncurses-term

# # if in china, add local pip mirrors
# {% if in_china %}
# RUN mkdir -p $HOME/.pip || true
# RUN echo '[global]' >> $HOME/.pip/pip.conf
# RUN echo 'index-url = http://mirrors.aliyun.com/pypi/simple' >> $HOME/.pip/pip.conf
# RUN echo 'trusted-host = mirrors.aliyun.com' >> $HOME/.pip/pip.conf
# {% endif %}

# install IsaacLab

ARG ISAACLAB_PATH="/isaaclab"
WORKDIR ${ISAACLAB_PATH}

ENV ISAACSIM_PATH="/isaac-sim"
ENV PYTHON_PATH="${ISAACSIM_PATH}/python.sh"

# add github to known hosts
RUN mkdir /root/.ssh && ssh-keyscan -t rsa github.com >> /root/.ssh/known_hosts

# [DEV] (remove private key usage)
# clone isaaclab repo
ADD isaaclab.pem /root/
RUN ssh-agent bash -c 'ssh-add /root/isaaclab.pem; git clone git@github.com:isaac-sim/IsaacLab.git .'
RUN git checkout "{{ isaaclab_git_checkpoint }}"

RUN ln -s ${ISAACSIM_PATH} _isaac_sim

# install IsaacLab
# RUN ./orbit.sh -i
RUN ./isaaclab.sh --extra

# create aliases for python
RUN echo "alias PYTHON_PATH=${PYTHON_PATH}" >> ${HOME}/.bashrc
RUN echo "alias python=${PYTHON_PATH}" >> ${HOME}/.bashrc

# RUN ${ISAACSIM_PYTHON_EXE} -c "import omni.isaac.isaaclab; print('Orbit configuration is now complete.')"

# link mapped folders to isaaclab path
RUN mkdir /results ; ln -s /results ${ISAACLAB_PATH}/
RUN mkdir /uploads ; ln -s /uploads ${ISAACLAB_PATH}/
RUN mkdir /workspace ; ln -s /workspace ${ISAACLAB_PATH}/

# customoize bash prompt
RUN echo "export PS1='\[\033[01;33m\][IsaacLab]\[\033[00m\]:\w\$ '" >>  $HOME/.bashrc

# # welcome message
RUN echo "echo '\\nWelcome to Isaac Lab!\\n'" >>  $HOME/.bashrc

ENTRYPOINT [""]
CMD ["/usr/bin/bash"]
