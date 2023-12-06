# region copyright
# Copyright 2023 NVIDIA Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# endregion

"""
Base deploy- command
"""

import os
import re

import click
import randomname
from pwgen import pwgen

from src.python.config import c as config
from src.python.debug import debug_break  # noqa
from src.python.utils import colorize_error, colorize_prompt


class DeployCommand(click.core.Command):
    """
    Defines common cli options for "deploy-*" commands.
    """

    @staticmethod
    def isaac_callback(ctx, param, value):
        """
        Called after --isaac option is parsed
        """
        # disable isaac instance type selection if isaac is disabled
        if value is False:
            for p in ctx.command.params:
                if p.name.startswith("isaac"):
                    p.prompt = None
        return value

    @staticmethod
    def deployment_name_callback(ctx, param, value):
        # validate
        if not re.match("^[a-z0-9\\-]{1,32}$", value):
            raise click.BadParameter(
                colorize_error(
                    "Only lower case letters, numbers and '-' are allowed."
                    + f" Length should be between 1 and 32 characters ({len(value)} provided)."
                )
            )

        return value

    @staticmethod
    def ngc_api_key_callback(ctx, param, value):
        """
        Validate NGC API key
        """

        # fix click bug
        if value is None:
            return value

        # allow "none" as a special value
        if "none" == value:
            return value

        # check if it contains what's allowed
        if not re.match("^[A-Za-z0-9]{32,}$", value):
            raise click.BadParameter(
                colorize_error("Key contains invalid characters or too short.")
            )

        return value

    @staticmethod
    def ngc_image_callback(ctx, param, value):
        """
        Called after parsing --isaac-image options are parsed
        """

        # ignore case
        value = value.lower()

        if not re.match(
            "^nvcr\\.io/[a-z0-9\\-_]+/([a-z0-9\\-_]+/)?[a-z0-9\\-_]+:[a-z0-9\\-_.]+$",
            value,
        ):
            raise click.BadParameter(
                colorize_error(
                    "Invalid image name. "
                    + "Expected: nvcr.io/<org>/[<team>/]<image>:<tag>"
                )
            )

        return value

    @staticmethod
    def oige_callback(ctx, param, value):
        """
        Called after parsing --oige option
        """

        if "" == value:
            return config["default_oige_git_checkpoint"]

        return value

    @staticmethod
    def orbit_callback(ctx, param, value):
        """
        Called after parsing --orbit option
        """

        if "" == value:
            return config["default_orbit_git_checkpoint"]

        return value

    def param_index(self, param_name):
        """
        Return index of parameter with given name.
        Useful for inserting new parameters at a specific position.
        """
        return list(
            filter(
                lambda param: param[1].name == param_name,
                enumerate(self.params),
            )
        )[0][0]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # add common options

        self.params.insert(
            len(self.params),
            click.core.Option(
                ("--debug/--no-debug",),
                default=False,
                show_default=True,
                help="Enable debug output.",
            ),
        )

        # --prefix
        self.params.insert(
            len(self.params),
            click.core.Option(
                ("--prefix",),
                default=config["default_prefix"],
                show_default=True,
                help="Prefix for all cloud resources.",
            ),
        )

        # --from-image/--not-from-image
        self.params.insert(
            len(self.params),
            click.core.Option(
                ("--from-image/--not-from-image",),
                default=False,
                show_default=True,
                help="Deploy from pre-built image, from bare OS otherwise.",
            ),
        )

        # --in-china
        self.params.insert(
            len(self.params),
            click.core.Option(
                ("--in-china",),
                type=click.Choice(["auto", "yes", "no"]),
                prompt=False,
                default="auto",
                show_default=True,
                help="Is deployment in China? (Local mirrors will be used.)",
            ),
        )

        self.params.insert(
            len(self.params),
            click.core.Option(
                ("--deployment-name", "--dn"),
                prompt=colorize_prompt(
                    '* Deployment Name (lower case letters, numbers and "-")'
                ),
                default=randomname.get_name,
                callback=DeployCommand.deployment_name_callback,
                show_default="<randomly generated>",
                help="Name of the deployment. Used to identify the created cloud resources and files.",
            ),
        )

        self.params.insert(
            len(self.params),
            click.core.Option(
                ("--existing",),
                type=click.Choice(
                    ["ask", "repair", "modify", "replace", "run_ansible"]
                ),
                default="ask",
                show_default=True,
                help="""What to do if deployment already exists:
                \n* 'repair' will try to fix broken deployment without applying new user parameters.
                \n* 'modify' will update user selected parameters and attempt to update existing cloud resources.
                \n* 'replace' will attempt to delete old deployment's cloud resources first.
                \n* 'run_ansible' will re-run Ansible playbooks.""",
            ),
        )

        self.params.insert(
            len(self.params),
            click.core.Option(
                ("--isaac/--no-isaac",),
                default=True,
                show_default="yes",
                prompt=colorize_prompt("* Deploy Isaac Sim?"),
                callback=DeployCommand.isaac_callback,
                help="Deploy Isaac Sim (BETA)?",
            ),
        )

        self.params.insert(
            len(self.params),
            click.core.Option(
                ("--isaac-image",),
                default=config["default_isaac_image"],
                prompt=colorize_prompt("* Isaac Sim docker image"),
                show_default=True,
                callback=DeployCommand.ngc_image_callback,
                help="Isaac Sim docker image to use.",
            ),
        )

        # --oige
        help = (
            "Install Omni Isaac Gym Envs? Valid values: 'no', "
            + "or <git ref in github.com/NVIDIA-Omniverse/OmniIsaacGymEnvs>."
        )
        self.params.insert(
            len(self.params),
            click.core.Option(
                ("--oige",),
                help=help,
                default="main",
                show_default=True,
                prompt=colorize_prompt("* " + help),
                callback=DeployCommand.oige_callback,
            ),
        )

        # --orbit
        help = (
            "[EXPERIMENTAL] Install Isaac Sim Orbit? Valid values: 'no', "
            + "or <git ref in github.com/NVIDIA-Omniverse/orbit>."
        )
        self.params.insert(
            len(self.params),
            click.core.Option(
                ("--orbit",),
                help=help,
                default="no",
                show_default=True,
                prompt=colorize_prompt("* " + help),
                callback=DeployCommand.orbit_callback,
            ),
        )

        self.params.insert(
            len(self.params),
            click.core.Option(
                ("--ngc-api-key",),
                type=str,
                prompt=colorize_prompt(
                    "* NGC API Key (can be obtained at https://ngc.nvidia.com/setup/api-key)"
                ),
                default=os.environ.get("NGC_API_KEY", ""),
                show_default='"NGC_API_KEY" environment variable',
                help="NGC API Key (can be obtained at https://ngc.nvidia.com/setup/api-key)",
                callback=DeployCommand.ngc_api_key_callback,
            ),
        )

        self.params.insert(
            len(self.params),
            click.core.Option(
                ("--ngc-api-key-check/--no-ngc-api-key-check",),
                default=True,
                help="Skip NGC API key validity check.",
            ),
        )

        self.params.insert(
            len(self.params),
            click.core.Option(
                ("--vnc-password",),
                default=lambda: pwgen(10),
                help="Password for VNC access to DRIVE Sim/Isaac Sim/etc.",
                show_default="<randomly generated>",
            ),
        )

        self.params.insert(
            len(self.params),
            click.core.Option(
                ("--system-user-password",),
                default=lambda: pwgen(10),
                help="System user password",
                show_default="<randomly generated>",
            ),
        )

        self.params.insert(
            len(self.params),
            click.core.Option(
                ("--ssh-port",),
                default=config["default_ssh_port"],
                help="SSH port for connecting to the deployed machines.",
                show_default=True,
            ),
        )

        # --upload/--no-upload
        self.params.insert(
            len(self.params),
            click.core.Option(
                ("--upload/--no-upload",),
                prompt=False,
                default=True,
                show_default=True,
                help=f"Upload user data from \"{config['uploads_dir']}\" to cloud "
                + f"instances (to \"{config['default_remote_uploads_dir']}\")?",
            ),
        )

        default_nucleus_admin_password = pwgen(10)

        # --omniverse-user
        self.params.insert(
            len(self.params),
            click.core.Option(
                ("--omniverse-user",),
                default=config["default_omniverse_user"],
                help="Username for accessing content on the Nucleus server.",
                show_default=True,
            ),
        )

        # --omniverse-password
        self.params.insert(
            len(self.params),
            click.core.Option(
                ("--omniverse-password",),
                default=default_nucleus_admin_password,
                help="Password for accessing content on the Nucleus server.",
                show_default="<randomly generated>",
            ),
        )
