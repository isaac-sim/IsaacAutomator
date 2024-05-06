#!/bin/bash

# build and launch https://github.com/isaac-sim/IsaacLab

# build docker image for Orbit
docker build -t isaaclab -f "{{ isaaclab_dir }}/isaaclab.dockerfile" "{{ isaaclab_dir }}"

clear

/home/{{ ansible_user }}/Desktop/isaacsim.sh --docker_image="isaaclab" --cmd="bash"
