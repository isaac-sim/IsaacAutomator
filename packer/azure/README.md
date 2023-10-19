# Running packer for Azure

See https://learn.microsoft.com/en-us/azure/virtual-machines/linux/build-image-with-packer

## 1. Create resource group for packer output

```sh
az group create -n isa.packer -l westus3
```

## 2. Create Azure service principal

```sh
export AZURE_SUBSCRIPTION_ID=`az account list | jq -r .[0].id`
az ad sp create-for-rbac \
  --role Contributor \
  --scopes /subscriptions/$AZURE_SUBSCRIPTION_ID \
  --query "{ client_id: appId, client_secret: password, tenant_id: tenant }"
```

## 3. Build image

Set env vars with credentials:

```sh
export AZURE_SUBSCRIPTION_ID="..."
export AZURE_TENANT_ID="..."
export AZURE_SP_CLIENT_ID="..."
export AZURE_SP_CLIENT_SECRET="..."
export NGC_API_KEY="..."
```

Alternatively you can pass them as variables in the packer command (`packer -var=varname=value...`).

Then launch image builds with:

```sh
packer build [-var=image_name=...] <folder>/
```

For example:

```
packer build isaac/
packer build -var=image_name=my_image_1 isaac/
```
