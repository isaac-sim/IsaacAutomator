#!/bin/bash

# build and launch https://github.com/NVIDIA-Omniverse/OmniIsaacGymEnvs

# build docker image for OmniIsaacGymEnvs
docker build -t omni-isaac-gym-envs -f "{{ omni_isaac_gym_envs_dir }}/omni-isaac-gym-envs.dockerfile" "{{ omni_isaac_gym_envs_dir }}"

clear

"{{ launch_scripts_dir }}/isaacsim.sh" --docker_image="omni-isaac-gym-envs" --cmd="bash"
