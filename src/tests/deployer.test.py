#!/usr/bin/env python3

import unittest
from pathlib import Path

from src.python.config import c
from src.python.deployer import Deployer


class Test_Deployer(unittest.TestCase):
    def setUp(self):
        self.config = c
        self.config["state_dir"] = f"{c['tests_dir']}/res/state"

        self.deployer = Deployer(
            params={
                "debug": False,
                "prefix": "isa",
                "from_image": False,
                "deployment_name": "test-1",
                "existing": "ask",
                "in_china": "no",
                "region": "us-east-1",
                "isaac": True,
                "isaac_workstation_instance_type": "g5.2xlarge",
                "isaac_image": "nvcr.io/nvidia/isaac-sim:2022.2.0",
                "vnc_password": "__vnc_password__",
                "ssh_port": 22,
                "upload": True,
                "aws_access_key_id": "__aws_access_key_id__",
                "aws_secret_access_key": "__aws_secret_access_key__",
                "ingress_cidrs": "auto",
            },
            config=self.config,
        )

    def tearDown(self):
        self.deployer = None

    def test_output_deployment_info(self):
        self.deployer.output_deployment_info(print_text=False)

        file_generated = f"{self.config['state_dir']}/test-1/info.txt"
        file_expected = f"{self.config['state_dir']}/test-1/info.expected.txt"

        file_generated = Path(file_generated).read_text()
        file_expected = Path(file_expected).read_text()

        self.assertEqual(file_generated, file_expected)


if __name__ == "__main__":
    unittest.main()
