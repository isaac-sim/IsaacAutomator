# Testing Private Isaac Lab repository (for internal NV QA)

1. Place a private key that you have registered in your Github account to `uploads/isaaclab.pem` (locally). This file will be used to check out the private repository of Isaac Lab.
2. Deploy an instance adding `--isaaclab-private-git=<path to repo, ending with .git>`. For example:
```sh
./deploy-aws --isaaclab-private-git="github.com/isaac-sim/IsaacLabPrivate.git"
```
3. Connect to an instance with NoMachine or noVNC.
4. Click on "Isaac Lab" desktop icon.
5. Try running samples and tests from the opened console.
