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

import pathlib
import subprocess

SELF_DIR = pathlib.Path(__file__).parent.resolve()


def check_ngc_access(ngc_api_key, org="", team="", verbose=False):
    """
    Checks if NGC API key is valid and user has access to DRIVE Sim.

    Returns:

    - 0 - all is fine
    - 100 - invalid api key
    - 102 - user is not in the team
    """

    proc = subprocess.run(
        [f"{SELF_DIR}/ngc_check.expect", ngc_api_key, org, team],
        capture_output=not verbose,
        timeout=60,
    )

    if proc.returncode not in [0, 100, 101, 102]:
        raise RuntimeError(
            f"Error checking NGC API Key. Return code: {proc.returncode}"
        )

    return proc.returncode
