#!/usr/bin/env python3

import tempfile
import unittest
from pathlib import Path

from src.python.config import c
from src.python.deployer import Deployer


def _make_deployer(state_dir=None, extra=None):
    """Build a Deployer with a minimal valid param set, optionally overridden."""
    config = c.copy()
    config["state_dir"] = state_dir or f"{c['tests_dir']}/res/state"

    params = {
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
    }
    if extra:
        params.update(extra)

    return Deployer(params=params, config=config)


class Test_Deployer(unittest.TestCase):
    def setUp(self):
        self.config = c
        self.config["state_dir"] = f"{c['tests_dir']}/res/state"
        self.deployer = _make_deployer()

    def tearDown(self):
        self.deployer = None

    def test_output_deployment_info(self):
        self.deployer.output_deployment_info(print_text=False)

        file_generated = f"{self.config['state_dir']}/test-1/info.txt"
        file_expected = f"{self.config['state_dir']}/test-1/info.expected.txt"

        file_generated = Path(file_generated).read_text()
        file_expected = Path(file_expected).read_text()

        self.assertEqual(file_generated, file_expected)


class Test_RecreateCommandLine(unittest.TestCase):
    def test_includes_string_options(self):
        deployer = _make_deployer()
        cmd = deployer.recreate_command_line(separator=" ")
        self.assertIn("--prefix isa", cmd)
        self.assertIn("--deployment-name test-1", cmd)
        self.assertIn("--region us-east-1", cmd)

    def test_quotes_strings_with_spaces(self):
        deployer = _make_deployer(extra={"region": "us east 1"})
        cmd = deployer.recreate_command_line(separator=" ")
        self.assertIn("'us east 1'", cmd)

    def test_boolean_flags(self):
        deployer = _make_deployer(extra={"upload": True, "from_image": False})
        cmd = deployer.recreate_command_line(separator=" ")
        self.assertIn("--upload", cmd)
        self.assertNotIn("--no-upload", cmd)
        # from-image uses --not- prefix when False
        self.assertIn("--not-from-image", cmd)


class Test_WriteTfvarsFile(unittest.TestCase):
    def test_writes_strings_lists_and_bools(self):
        deployer = _make_deployer()
        with tempfile.TemporaryDirectory() as tmp:
            path = f"{tmp}/.tfvars"
            deployer._write_tfvars_file(
                path=path,
                tfvars={
                    "prefix": "isa",
                    "isaac_enabled": True,
                    "from_image": False,
                    "ingress_cidrs": ["10.0.0.0/8", "1.2.3.4/32"],
                    "ssh_port": 22,
                },
            )
            content = Path(path).read_text()

        self.assertIn('prefix = "isa"', content)
        # booleans are stringified then quoted; terraform parses them into bool vars
        self.assertIn('isaac_enabled = "true"', content)
        self.assertIn('from_image = "false"', content)
        self.assertIn('ingress_cidrs = ["10.0.0.0/8", "1.2.3.4/32"]', content)
        self.assertIn("ssh_port = 22", content)

    def test_escapes_quotes_in_strings(self):
        deployer = _make_deployer()
        with tempfile.TemporaryDirectory() as tmp:
            path = f"{tmp}/.tfvars"
            deployer._write_tfvars_file(
                path=path,
                tfvars={"password": 'has "quotes"'},
            )
            content = Path(path).read_text()
        self.assertIn(r'password = "has \"quotes\""', content)

    def test_normalizes_hyphen_keys_to_underscores(self):
        deployer = _make_deployer()
        with tempfile.TemporaryDirectory() as tmp:
            path = f"{tmp}/.tfvars"
            deployer._write_tfvars_file(
                path=path,
                tfvars={"resource-group": "rg-1"},
            )
            content = Path(path).read_text()
        self.assertIn('resource_group = "rg-1"', content)


class Test_InChinaConversion(unittest.TestCase):
    def test_yes_becomes_true(self):
        deployer = _make_deployer(extra={"in_china": "yes"})
        self.assertTrue(deployer.params["in_china"])

    def test_no_becomes_false(self):
        deployer = _make_deployer(extra={"in_china": "no"})
        self.assertFalse(deployer.params["in_china"])

    def test_auto_becomes_false(self):
        deployer = _make_deployer(extra={"in_china": "auto"})
        self.assertFalse(deployer.params["in_china"])


if __name__ == "__main__":
    unittest.main()
