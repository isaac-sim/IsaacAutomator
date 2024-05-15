#!/bin/bash

# default parameter values

# isaac sim startup command
CMD="bash uploads/pass-creds-to-container.sh ;apt-get update && apt-get install -y ffmpeg; /isaac-sim/kit/kit \
      /isaac-sim/apps/omni.isaac.sim.kit \
      --ext-folder /isaac-sim/apps \
      --allow-root"

DISPLAY=":0"
CONTAINER_NAME="isaacsim"
OUT_DIR="{{ results_dir }}"
UPLOADS_DIR="{{ uploads_dir }}"
WORKSPACE_DIR="{{ workspace_dir }}"
OMNI_USER="{{ omniverse_user }}"
OMNI_PASS="{{ omniverse_password }}"
DOCKER_IMAGE="{{ isaac_image }}"
CACHE_DIR="{{ isaac_cache_dir }}"
NUCLEUS_SERVER_NAME="{{ nucleus_uri }}"

# detect vulkan location
if [ -f /usr/share/vulkan/icd.d/nvidia_icd.json ]
then
  VULKAN_DIR="/usr/share/vulkan"
elif [ -f /etc/vulkan/icd.d/nvidia_icd.json ]
then
  VULKAN_DIR="/etc/vulkan"
else
  echo "ERROR: Could not detect Vulkan installation directory"
  exit 1
fi

# find .Xauthority
XAUTHORITY_LOCATION=$(systemctl --user show-environment | grep XAUTHORITY | cut -c 12-)

# process named arguments
while [ $# -gt 0 ]; do
  case "$1" in
      
    --help|-h)
      echo "Usage: `basename $0` \\"
      echo "  [--command=..] \\"
      echo "  [--out_dir=..] \\"
      echo "  [--omni_user=..] \\"
      echo "  [--omni_pass=..] \\"
      echo "  [--docker_image=..] \\"
      echo "  [--container_name=..] \\"
      echo "  [--nucleus_server=..]"
      echo
      echo "Defaults: "
      echo "  --command='${CMD}'"
      echo "  --out_dir='${OUT_DIR}'"
      echo "  --omni_user='${OMNI_USER}'"
      echo "  --omni_pass='${OMNI_PASS}'"
      echo "  --docker_image='${DOCKER_IMAGE}'"
      echo "  --container_name='${CONTAINER_NAME}'"
      echo "  --nucleus_server='${NUCLEUS_SERVER_NAME}'"
      exit
      ;;

    --debug)
      set -x
      ;;

    --nucleus=*|--nucleus_server=*|--nucleus_server_name=*|--nucleus_url=*|--nucleus_ip=*)
      NUCLEUS_SERVER_NAME="${1#*=}"
      ;;

    --user=*|--username=*|--omni_user=*)
      OMNI_USER="${1#*=}"
      ;;
      
    --pass=*|--password=*|--omni_pass=*)
      OMNI_PASS="${1#*=}"
      ;;

    --image=*|--docker_image=*)
      DOCKER_IMAGE="${1#*=}"
      ;;

    --out=*|--output=*|--out_dir=*|--output_dir=*)
      OUT_DIR="${1#*=}"
      ;;

    --uploads_dir=*)
      UPLOADS_DIR="${1#*=}"
      ;;

    --workspace_dir=*)
      WORKSPACE_DIR="${1#*=}"
      ;;

    --display=*)
      DISPLAY="${1#*=}"
      ;;

    --cmd=*|--command=*)
      CMD="${1#*=}"
      ;;

    --container-name=*|--name=*)
      CONTAINER_NAME="${1#*=}"
      ;;

  esac
  shift
done

# create cache dir if it doesn't exist, assign permissions
[ ! -d "${CACHE_DIR}" ] && mkdir -pv "${CACHE_DIR}"
[ -d "${CACHE_DIR}" ] && chmod 0777 "${CACHE_DIR}"
mkdir -pv "${CACHE_DIR}/ov" "${CACHE_DIR}/pip" "${CACHE_DIR}/glcache" "${CACHE_DIR}/computecache" "${CACHE_DIR}/logs" "${CACHE_DIR}/config" "${CACHE_DIR}/data" "${CACHE_DIR}/documents" 2>/dev/null

# create output/uploads/workspace dirs if it doesn't exist
for d in "${OUT_DIR}" "${UPLOADS_DIR}" "${WORKSPACE_DIR}"; do
  [ ! -d "${d}" ] && mkdir -pv "${d}"
done

# kill any existing container
docker kill $CONTAINER_NAME 2>/dev/null

docker run \
  --network=host -it --rm --gpus all \
  \
  --env "ACCEPT_EULA=Y" \
  --env OMNI_USER="$OMNI_USER" \
  --env OMNI_PASS="$OMNI_PASS" \
  \
  -v "${VULKAN_DIR}/icd.d/nvidia_icd.json":/etc/vulkan/icd.d/nvidia_icd.json \
  -v "${VULKAN_DIR}/implicit_layer.d/nvidia_layers.json":/etc/vulkan/implicit_layer.d/nvidia_layers.json \
  -v /usr/share/glvnd/egl_vendor.d/10_nvidia.json:/usr/share/glvnd/egl_vendor.d/10_nvidia.json \
  \
  -v "${CACHE_DIR}/ov":/root/.cache/ov:rw \
  -v "${CACHE_DIR}/pip":/root/.cache/pip:rw \
  -v "${CACHE_DIR}/glcache":/root/.cache/nvidia/GLCache:rw \
  -v "${CACHE_DIR}/computecache":/root/.nv/ComputeCache:rw \
  -v "${CACHE_DIR}/logs":/root/.nvidia-omniverse/logs:rw \
  -v "${CACHE_DIR}/config":/root/.nvidia-omniverse/config:rw \
  -v "${CACHE_DIR}/data":/root/.local/share/ov/data:rw \
  -v "${CACHE_DIR}/docs":/root/Documents:rw \
  \
  -v "${OUT_DIR}":/results \
  -v "${UPLOADS_DIR}":/uploads \
  -v "${UPLOADS_DIR}/credentials:/root/.aws/credentials" \  
  -v "${WORKSPACE_DIR}":/workspace \
  \
  -v "/tmp/.X11-unix:/tmp/.X11-unix" \
  -v "${XAUTHORITY_LOCATION}:/root/.Xauthority" \
  -v /etc/xdg:/etc/xdg \
  --env XDG_CONFIG_DIRS \
  --env DISPLAY \
  \
  --name $CONTAINER_NAME \
  --entrypoint "/bin/sh" \
  $DOCKER_IMAGE \
  -c "$CMD"
