#!/usr/bin/env python3

import importlib.machinery
import importlib.util
import unittest
from pathlib import Path
from unittest import mock

# the ./import script has no .py extension, so load it by path
_IMPORT_SCRIPT = Path(__file__).resolve().parents[2] / "import"
_loader = importlib.machinery.SourceFileLoader("import_script", str(_IMPORT_SCRIPT))
_spec = importlib.util.spec_from_loader("import_script", _loader)
import_script = importlib.util.module_from_spec(_spec)
_loader.exec_module(import_script)


def _run_with_fake_shell(fn, *args):
    """Run fn with shell_command stubbed out; return the commands it issued."""

    calls = []

    def fake_shell_command(command, *a, **kw):
        calls.append(command)
        res = mock.Mock()
        res.returncode = 0
        res.stdout = b""
        return res

    with mock.patch.object(import_script, "shell_command", fake_shell_command):
        fn(*args)

    return calls


class Test_AwsImportDeployment(unittest.TestCase):
    RESOURCES = {
        "key_pair": "isaacautomator.dn.keypair",
        "vpc": "vpc-0123",
        "internet_gateway": "igw-0123",
        "route_table": "rtb-0123",
        "subnet": "subnet-0123",
        "security_group": "sg-0123",
        "instance": "i-0123",
        "eip": "eipalloc-0123",
    }

    def _import_command(self, calls, addr):
        matches = [c for c in calls if "terraform import" in c and addr in c]
        self.assertEqual(len(matches), 1, f"expected one import of {addr}")
        return matches[0]

    def test_default_route_table_is_imported_by_vpc_id(self):
        calls = _run_with_fake_shell(
            import_script._aws_import_deployment,
            "isaacautomator",
            "dn",
            "us-east-1",
            dict(self.RESOURCES),
        )
        cmd = self._import_command(
            calls, "module.vpc.aws_default_route_table.vpc_route_table"
        )
        self.assertTrue(cmd.endswith("'vpc-0123'"), cmd)
        self.assertNotIn("rtb-0123", cmd)

    def test_other_resources_keep_their_own_ids(self):
        calls = _run_with_fake_shell(
            import_script._aws_import_deployment,
            "isaacautomator",
            "dn",
            "us-east-1",
            dict(self.RESOURCES),
        )
        for addr, rid in [
            ("module.vpc.aws_vpc.vpc", "vpc-0123"),
            ("module.isaac_workstation[0].aws_instance.instance", "i-0123"),
            ("module.isaac_workstation[0].aws_eip.eip", "eipalloc-0123"),
        ]:
            self.assertTrue(self._import_command(calls, addr).endswith(f"'{rid}'"))


class Test_NoPrivateKeyImport(unittest.TestCase):
    """tls_private_key cannot be imported, and trying it echoed a private key."""

    def _assert_no_key_import(self, calls):
        for cmd in calls:
            self.assertNotIn("tls_private_key", cmd)
            self.assertNotIn("PRIVATE KEY", cmd)
            self.assertNotIn("openssl genrsa", cmd)

    def test_aws(self):
        self._assert_no_key_import(
            _run_with_fake_shell(
                import_script._aws_import_deployment,
                "isaacautomator",
                "dn",
                "us-east-1",
                dict(Test_AwsImportDeployment.RESOURCES),
            )
        )

    def test_azure(self):
        self._assert_no_key_import(
            _run_with_fake_shell(
                import_script._azure_import_deployment,
                "isaacautomator",
                "dn",
                "westus3",
                {},
            )
        )

    def test_gcp(self):
        self._assert_no_key_import(
            _run_with_fake_shell(
                import_script._gcp_import_deployment,
                "isaacautomator",
                "dn",
                "my-project",
                "us-central1-a",
                {},
            )
        )


if __name__ == "__main__":
    unittest.main()
