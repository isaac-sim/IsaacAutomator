# Running packer for AWS

Set env vars with credentials:

```sh
export AWS_ACCESS_KEY_ID ="..."
export AWS_SECRET_ACCESS_KEY ="..."
export NGC_API_KEY="..." # optional
```

Alternatively you can pass them as variables in the packer command (`packer -var=varname=value...`).

Then launch image builds with:

```sh
packer build [-force] [-var=aws_region="us-east-1"] [-var=image_name="..."] [-var=system_user_password="..."] [-var=vnc_password="..."] <folder>/
```

For example:

```sh
packer build -force \
-var=aws_region="us-east-1" \
-var=image_name=ovami-test-1 \
-var=system_user_password="nvidia123" \
-var=vnc_password="nvidia123" \
/app/packer/aws/ovami
```
