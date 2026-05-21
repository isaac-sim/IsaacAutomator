# Running Packer for Azure

See <https://learn.microsoft.com/en-us/azure/virtual-machines/linux/build-image-with-packer>.

The recommended way to build Azure images is via the top-level wrapper:

```sh
./image-azure
```

The wrapper handles `az login`, creates the destination resource group if it is
missing, exports the credentials Packer expects, and invokes `packer build`.

## Manual build

If you need to invoke Packer directly, log in with the Azure CLI first:

```sh
az login
export AZURE_SUBSCRIPTION_ID="$(az account show --query id -o tsv)"
```

Then create the resource group used to store the captured managed image
(default name: `isaac_automator.packer`):

```sh
az group create -n isaac_automator.packer -l westus3
```

Initialize Packer plugins and run the build:

```sh
cd /app/src/packer/azure
packer init isaac-workstation.pkr.hcl
packer build \
  -var=version=v4.0.0-rc5 \
  [-var=image_name=my-image-name] \
  isaac-workstation.pkr.hcl
```

The built image is named `isaac_automator.isaacworkstation.<image_name>` and is
placed in `--managed-image-resource-group-name` (default
`isaac_automator.packer`).
