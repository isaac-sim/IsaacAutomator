#!/usr/bin/env python3

import contextlib
import io
import subprocess
import unittest
from unittest import mock

from src.python.utils import (
    format_cloud_name,
    format_instance_role,
    redact_url_credentials,
    shell_command,
    subnet_from_ip,
)


class Test_SubnetFromIp(unittest.TestCase):
    def test_slash_24(self):
        self.assertEqual(subnet_from_ip("10.0.1.42", "24"), "10.0.1.0/24")

    def test_slash_16(self):
        self.assertEqual(subnet_from_ip("10.0.1.42", "16"), "10.0.0.0/16")

    def test_slash_8(self):
        self.assertEqual(subnet_from_ip("10.0.1.42", "8"), "10.0.0.0/8")

    def test_unsupported_mask_raises(self):
        with self.assertRaises(Exception):
            subnet_from_ip("10.0.1.42", "12")


class Test_FormatCloudName(unittest.TestCase):
    def test_known_clouds(self):
        self.assertEqual(format_cloud_name("aws"), "AWS")
        self.assertEqual(format_cloud_name("azure"), "Azure")
        self.assertEqual(format_cloud_name("gcp"), "GCP")
        self.assertEqual(format_cloud_name("alicloud"), "Alibaba Cloud")

    def test_unknown_cloud_passthrough(self):
        self.assertEqual(format_cloud_name("oracle"), "oracle")


class Test_FormatInstanceRole(unittest.TestCase):
    def test_known_role(self):
        self.assertEqual(format_instance_role("isaac_workstation"), "Isaac Workstation")

    def test_unknown_role_passthrough(self):
        self.assertEqual(format_instance_role("other"), "other")


class Test_RedactUrlCredentials(unittest.TestCase):
    def test_token_only_userinfo(self):
        self.assertEqual(
            redact_url_credentials("https://ghp_abc123@github.com/o/r"),
            "https://***@github.com/o/r",
        )

    def test_user_and_password(self):
        self.assertEqual(
            redact_url_credentials("https://user:ghp_abc123@github.com/o/r.git"),
            "https://***@github.com/o/r.git",
        )

    def test_scp_form_is_not_credentials(self):
        # "git@host:path" is the ssh shorthand, not a secret
        self.assertEqual(
            redact_url_credentials("git@github.com:o/r.git"),
            "git@github.com:o/r.git",
        )

    def test_url_without_credentials_is_untouched(self):
        self.assertEqual(
            redact_url_credentials("https://github.com/o/r"),
            "https://github.com/o/r",
        )

    def test_every_occurrence_is_masked(self):
        self.assertEqual(
            redact_url_credentials("https://t1@h/a and https://t2@h/b"),
            "https://***@h/a and https://***@h/b",
        )

    def test_empty_and_none_pass_through(self):
        self.assertEqual(redact_url_credentials(""), "")
        self.assertIsNone(redact_url_credentials(None))


class Test_ShellCommandDoesNotEchoCredentials(unittest.TestCase):
    """
    The top-level scripts re-exec themselves into the container as
    "./run '<full argv>'", so a token passed in a repo url reaches this echo.
    """

    SECRET = "ghp_LEAKME12345"

    def _run(self, command, **kwargs):
        seen = {}
        attrs = {"returncode": 0, "stdout": None, "stderr": None}
        attrs.update(kwargs)

        def fake(cmd, **kw):
            seen["cmd"] = cmd
            return mock.Mock(**attrs)

        out, err = io.StringIO(), io.StringIO()
        with mock.patch.object(subprocess, "run", side_effect=fake):
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                shell_command(command, verbose=True)
        return seen.get("cmd"), out.getvalue() + err.getvalue()

    def test_echoed_command_masks_the_token(self):
        cmd = (
            f"./run './deploy-aws --isaacsim-git-repo"
            f" https://{self.SECRET}@github.com/o/r --isaacsim develop'"
        )
        _, printed = self._run(cmd)
        self.assertNotIn(self.SECRET, printed)
        self.assertIn("***@github.com", printed)

    def test_executed_command_keeps_the_real_token(self):
        # redacting the command itself would break the re-exec into the container
        cmd = f"./run './deploy-aws --isaacsim-git-repo https://{self.SECRET}@h/o/r'"
        executed, _ = self._run(cmd)
        self.assertIn(self.SECRET, executed)

    def test_cwd_variant_masks_the_token(self):
        seen = {}

        def fake(cmd, **kw):
            seen["cmd"] = cmd
            return mock.Mock(returncode=0, stdout=None, stderr=None)

        buf = io.StringIO()
        with mock.patch.object(subprocess, "run", side_effect=fake):
            with contextlib.redirect_stdout(buf):
                shell_command(
                    f"git clone https://{self.SECRET}@github.com/o/r",
                    verbose=True,
                    cwd="/tmp",
                )
        self.assertNotIn(self.SECRET, buf.getvalue())
        self.assertIn("cd /tmp", buf.getvalue())

    def test_child_stdout_is_scrubbed(self):
        _, printed = self._run(
            "cmd", stdout=f"cloning https://{self.SECRET}@github.com/o/r\n".encode()
        )
        self.assertNotIn(self.SECRET, printed)

    def test_child_stderr_is_scrubbed_on_failure(self):
        def fake(cmd, **kw):
            return mock.Mock(
                returncode=128,
                stdout=None,
                stderr=f"fatal: cannot read https://{self.SECRET}@h/o/r\n".encode(),
            )

        buf = io.StringIO()
        with mock.patch.object(subprocess, "run", side_effect=fake):
            with contextlib.redirect_stderr(buf):
                with self.assertRaises(SystemExit):
                    shell_command("cmd", verbose=True)
        self.assertNotIn(self.SECRET, buf.getvalue())

    def test_quiet_mode_prints_nothing(self):
        _, printed = self._run(f"./run 'x https://{self.SECRET}@h/o/r'")
        self.assertNotIn(self.SECRET, printed)


if __name__ == "__main__":
    unittest.main()
