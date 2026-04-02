#!/bin/bash

# build and launch https://github.com/isaac-sim/IsaacLab

# build docker image for Isaac Lab
docker build -t isaaclab -f "{{ isaaclab_dir }}/isaaclab.dockerfile" "{{ isaaclab_dir }}"

clear

"{{ launch_scripts_dir }}/isaacsim.sh" --docker_image="isaaclab" --cmd="bash"
