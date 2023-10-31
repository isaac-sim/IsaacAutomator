#!/bin/bash

# build and launch https://github.com/NVIDIA-Omniverse/OmniIsaacGymEnvs

MY_DIR=$(realpath $(dirname ${BASH_SOURCE}))

# build docker image for OmniIsaacGymEnvs
docker build -t omni-isaac-gym-envs -f "{{ omni_isaac_gym_envs_dir }}/omni-isaac-gym-envs.dockerfile" "{{ omni_isaac_gym_envs_dir }}"

clear

/home/{{ ansible_user }}/Desktop/isaacsim.sh --docker_image="omni-isaac-gym-envs" --cmd="bash"
