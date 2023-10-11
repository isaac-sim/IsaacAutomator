#!/bin/bash

# launch shell inside isaacsim contaner

MY_DIR=$(realpath $(dirname ${BASH_SOURCE}))
${MY_DIR}/isaacsim.sh --cmd="bash"
