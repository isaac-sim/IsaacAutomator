# Development Tips

## Building contaner for development

```sh
docker build -t auto-isaac \
  --build-arg WITH_PACKER=true \
  --build-arg WITH_GIT=true \
  --platform linux/x86_64 \ # on Apple Silicon Macs when using Docker Desktop
  .
```

## Updating pre-built images

### AWS

Refer to [../packer/aws/README.md](../packer/aws/README.md) for pre-requisites. Then:

```sh
packer build -force /app/packer/aws/isaac
...
```

### Azure

Refer to [../packer/azure/README.md](../packer/azure/README.md) for pre-requisites. Then:

```sh
packer build -force /app/packer/azure/isaac
...
```
