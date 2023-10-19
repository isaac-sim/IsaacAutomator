
# Isaac Automation OSS Contribution Rules

- [Development Tips](#development-tips)
  - [Building Docker Contaner for Development](#building-docker-contaner-for-development)
  - [Updating Pre-Built VM Images](#updating-pre-built-vm-images)
    - [Azure](#azure)
- [Issue Tracking](#issue-tracking)
- [Coding Guidelines](#coding-guidelines)
  - [Formatting and Linting](#formatting-and-linting)
  - [General](#general)
- [Pull Requests](#pull-requests)
- [Signing Your Work](#signing-your-work)

## Development Tips

### Building Docker Contaner for Development

```sh
docker build -t auto-isaac \
  --build-arg WITH_PACKER=true \
  --build-arg WITH_GIT=true \
  --platform linux/x86_64 \ # on Apple Silicon Macs when using Docker Desktop
  .
```

### Updating Pre-Built VM Images

Pre-built VM images are created using [Packer](https://www.packer.io/) and can be used to accelerate deployment of the app instances by skipping the time-consuming installation and configuration steps. To use pre-built images, add `--from-image` flag to the `deploy-*` commands.

```sh

#### AWS

Refer to [../packer/aws/README.md](packer/aws/README.md) for pre-requisites. Then:

```sh
packer build -force /app/packer/aws/isaac
...
```

#### Azure

Refer to [../packer/azure/README.md](packer/azure/README.md) for pre-requisites. Then:

```sh
packer build -force /app/packer/azure/isaac
...
```

## Issue Tracking

- All enhancement, bugfix, or change requests must begin with the creation of a [Isaac Automation Issue Request](https://github.com/nvidia/Isaac-Automation/issues).

- The issue request must be reviewed by Isaac Automation engineers and approved prior to code review.

## Coding Guidelines

Please follow the existing conventions in the relevant file, submodule, module, and project when you add new code or when you extend/fix existing functionality.

### Formatting and Linting

- Make sure your editor is using the included `.editorconfig` file for indentation, line endings, etc.

- Use the following formatters and linting tools for the respective languages:
  
  - Python: [black](<https://github.com/psf/black>), [isort](<https://github.com/pycqa/isort/>), [flake8](https://github.com/pycqa/flake8)
  - Terraform: [terraform fmt](<https://www.terraform.io/docs/commands/fmt.html>)
  - Ansible: [ansible-lint](<https://github.com/ansible/ansible-lint>)
  - Packer: [packer fmt](<https://www.packer.io/docs/commands/fmt.html>)

Project includes settings and recommended extensions for [Visual Studio Code](https://code.visualstudio.com/) which make it easier following the formatting linting and guidelines.

### General

- Avoid introducing unnecessary complexity into existing code so that maintainability and readability are preserved.

- Try to keep pull requests (PRs) as concise as possible:
  - Avoid committing commented-out code.
  - Wherever possible, each PR should address a single concern. If there are several otherwise-unrelated things that should be fixed to reach a desired endpoint, our recommendation is to open several PRs and indicate the dependencies in the description. The more complex the changes are in a single PR, the more time it will take to review those changes.

- Write commit titles using imperative mood and [these rules](https://chris.beams.io/posts/git-commit/), and reference the Issue number corresponding to the PR. Following is the recommended format for commit texts:

```text
#<Issue Number> - <Commit Title>

<Commit Body>
```

- All OSS components must contain accompanying documentation (READMEs) describing the functionality, dependencies, and known issues.

- Accompanying tests are highly desireable and recommended. If the test is not possible or not feasible to implement, please provide a sample usage information.

- Make sure that you can contribute your work to open source (no license and/or patent conflict is introduced by your code). You will need to [`sign`](#signing-your-work) your commit.

- Thanks in advance for your patience as we review your contributions; we do appreciate them!

## Pull Requests

Developer workflow for code contributions is as follows:

1. Developers must first [fork](https://help.github.com/en/articles/fork-a-repo) the [upstream](https://github.com/nvidia/Isaac-Automation) Isaac Automation OSS repository.

1. Git clone the forked repository and push changes to the personal fork.
  
    ```bash
    git clone https://github.com/YOUR_USERNAME/YOUR_FORK.git Isaac-Automation
    # Checkout the targeted branch and commit changes
    # Push the commits to a branch on the fork (remote).
    git push -u origin <local-branch>:<remote-branch>
    ```

1. Once the code changes are staged on the fork and ready for review, a [Pull Request](https://help.github.com/en/articles/about-pull-requests) (PR) can be [requested](https://help.github.com/en/articles/creating-a-pull-request) to merge the changes from a branch of the fork into a selected branch of upstream.

## Signing Your Work

- We require that all contributors "sign-off" on their commits. This certifies that the contribution is your original work, or you have rights to submit it under the same license, or a compatible license.

- Any contribution which contains commits that are not Signed-Off will not be accepted.

- To sign off on a commit you simply use the `--signoff` (or `-s`) option when committing your changes:

  ```bash
  git commit -s -m "Add cool feature."
  ```

  This will append the following to your commit message:

  ```text
  Signed-off-by: Your Name <your@email.com>
  ```

- Full text of the DCO:

  ```text
  Developer Certificate of Origin
  Version 1.1
  
  Copyright (C) 2004, 2006 The Linux Foundation and its contributors.
  1 Letterman Drive
  Suite D4700
  San Francisco, CA, 94129
  
  Everyone is permitted to copy and distribute verbatim copies of this license document, but changing it is not allowed.

  Developer's Certificate of Origin 1.1
  
  By making a contribution to this project, I certify that:
  
  (a) The contribution was created in whole or in part by me and I have the right to submit it under the open source license indicated in the file; or
  
  (b) The contribution is based upon previous work that, to the best of my knowledge, is covered under an appropriate open source license and I have the right under that license to submit that work with modifications, whether created in whole or in part by me, under the same open source license (unless I am permitted to submit under a different license), as indicated in the file; or
  
  (c) The contribution was provided directly to me by some other person who certified (a), (b) or (c) and I have not modified it.
  
  (d) I understand and agree that this project and the contribution are public and that a record of the contribution (including all personal information I submit with it, including my sign-off) is maintained indefinitely and may be redistributed consistent with this project or the open source license(s) involved.
  ```
