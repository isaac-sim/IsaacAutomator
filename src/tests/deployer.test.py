#!/usr/bin/env python3

import shutil
import tempfile
import unittest
from pathlib import Path

from src.python.config import c
from src.python.deployer import Deployer

# Base parameter set used by the helper below.
_BASE_PARAMS = {
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


def _make_deployer(state_dir, extra=None):
    """
    Build a Deployer with a minimal valid param set, optionally overridden.
    Callers MUST pass an isolated state_dir so the Deployer's __del__
    hook (save_meta) does not mutate checked-in fixtures.
    """
    config = c.copy()
    config["state_dir"] = state_dir

    params = dict(_BASE_PARAMS)
    if extra:
        params.update(extra)

    return Deployer(params=params, config=config)


class Test_Deployer(unittest.TestCase):
    """
    Reads from the checked-in test-1 fixture but writes outputs into an
    isolated temp dir so the fixture files stay untouched. We copy the
    fixture into the temp dir before running.
    """

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        fixture_src = Path(c["tests_dir"]) / "res" / "state" / "test-1"
        fixture_dst = Path(self.tmp) / "test-1"
        shutil.copytree(fixture_src, fixture_dst)
        self.deployer = _make_deployer(state_dir=self.tmp)

    def tearDown(self):
        self.deployer = None
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_output_deployment_info(self):
        self.deployer.output_deployment_info(print_text=False)

        file_generated = Path(self.tmp) / "test-1" / "info.txt"
        file_expected = Path(self.tmp) / "test-1" / "info.expected.txt"

        self.assertEqual(file_generated.read_text(), file_expected.read_text())


class Test_RecreateCommandLine(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_includes_string_options(self):
        deployer = _make_deployer(state_dir=self.tmp)
        cmd = deployer.recreate_command_line(separator=" ")
        self.assertIn("--prefix isa", cmd)
        self.assertIn("--deployment-name test-1", cmd)
        self.assertIn("--region us-east-1", cmd)

    def test_quotes_strings_with_spaces(self):
        deployer = _make_deployer(state_dir=self.tmp, extra={"region": "us east 1"})
        cmd = deployer.recreate_command_line(separator=" ")
        self.assertIn("'us east 1'", cmd)

    def test_boolean_flags(self):
        deployer = _make_deployer(
            state_dir=self.tmp, extra={"upload": True, "from_image": False}
        )
        cmd = deployer.recreate_command_line(separator=" ")
        self.assertIn("--upload", cmd)
        self.assertNotIn("--no-upload", cmd)
        # from-image uses --not- prefix when False
        self.assertIn("--not-from-image", cmd)


class Test_WriteTfvarsFile(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_writes_strings_lists_and_bools(self):
        deployer = _make_deployer(state_dir=self.tmp)
        path = f"{self.tmp}/.tfvars"
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
        deployer = _make_deployer(state_dir=self.tmp)
        path = f"{self.tmp}/.tfvars"
        deployer._write_tfvars_file(
            path=path,
            tfvars={"password": 'has "quotes"'},
        )
        content = Path(path).read_text()
        self.assertIn(r'password = "has \"quotes\""', content)

    def test_normalizes_hyphen_keys_to_underscores(self):
        deployer = _make_deployer(state_dir=self.tmp)
        path = f"{self.tmp}/.tfvars"
        deployer._write_tfvars_file(
            path=path,
            tfvars={"resource-group": "rg-1"},
        )
        content = Path(path).read_text()
        self.assertIn('resource_group = "rg-1"', content)


class Test_InChinaConversion(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_yes_becomes_true(self):
        deployer = _make_deployer(state_dir=self.tmp, extra={"in_china": "yes"})
        self.assertTrue(deployer.params["in_china"])

    def test_no_becomes_false(self):
        deployer = _make_deployer(state_dir=self.tmp, extra={"in_china": "no"})
        self.assertFalse(deployer.params["in_china"])

    def test_auto_becomes_false(self):
        deployer = _make_deployer(state_dir=self.tmp, extra={"in_china": "auto"})
        self.assertFalse(deployer.params["in_china"])


if __name__ == "__main__":
    unittest.main()
