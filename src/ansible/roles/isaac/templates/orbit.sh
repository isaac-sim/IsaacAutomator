#!/bin/bash

# build and launch https://github.com/NVIDIA-Omniverse/Orbit

# build docker image for Orbit
docker build -t orbit -f "{{ orbit_dir }}/orbit.dockerfile" "{{ orbit_dir }}"

clear

"{{ launch_scripts_dir }}/isaacsim.sh" --docker_image="orbit" --cmd="bash"
