#!/usr/bin/env python3

import io
import json
import os
import unittest
from contextlib import redirect_stdout
from unittest import mock

from src.python.aws import (
    _aws_env_credentials_set,
    _aws_export_credentials,
    _aws_sso_login,
    _aws_sso_profile_configured,
    _aws_use_device_code,
    aws_cli_set,
    aws_load_credentials,
)


class Test_AwsEnvCredentialsSet(unittest.TestCase):
    def test_both_set(self):
        with mock.patch.dict(
            os.environ,
            {"AWS_ACCESS_KEY_ID": "AKIA...", "AWS_SECRET_ACCESS_KEY": "secret"},
            clear=False,
        ):
            self.assertTrue(_aws_env_credentials_set())

    def test_only_id_set(self):
        env = dict(os.environ)
        env["AWS_ACCESS_KEY_ID"] = "AKIA..."
        env.pop("AWS_SECRET_ACCESS_KEY", None)
        with mock.patch.dict(os.environ, env, clear=True):
            self.assertFalse(_aws_env_credentials_set())

    def test_only_secret_set(self):
        env = dict(os.environ)
        env.pop("AWS_ACCESS_KEY_ID", None)
        env["AWS_SECRET_ACCESS_KEY"] = "secret"
        with mock.patch.dict(os.environ, env, clear=True):
            self.assertFalse(_aws_env_credentials_set())

    def test_neither_set(self):
        env = dict(os.environ)
        env.pop("AWS_ACCESS_KEY_ID", None)
        env.pop("AWS_SECRET_ACCESS_KEY", None)
        with mock.patch.dict(os.environ, env, clear=True):
            self.assertFalse(_aws_env_credentials_set())

    def test_empty_strings_are_unset(self):
        with mock.patch.dict(
            os.environ,
            {"AWS_ACCESS_KEY_ID": "", "AWS_SECRET_ACCESS_KEY": ""},
            clear=False,
        ):
            self.assertFalse(_aws_env_credentials_set())


class Test_AwsLoadCredentials(unittest.TestCase):
    def test_env_vars_take_precedence(self):
        with mock.patch.dict(
            os.environ,
            {
                "AWS_ACCESS_KEY_ID": "AKIAENV",
                "AWS_SECRET_ACCESS_KEY": "envsecret",
                "AWS_SESSION_TOKEN": "envtoken",
                "AWS_DEFAULT_REGION": "eu-west-1",
            },
            clear=False,
        ):
            creds = aws_load_credentials(verbose=False)

        self.assertEqual(creds["aws_access_key_id"], "AKIAENV")
        self.assertEqual(creds["aws_secret_access_key"], "envsecret")
        self.assertEqual(creds["aws_session_token"], "envtoken")
        self.assertEqual(creds["region"], "eu-west-1")


class Test_AwsSsoProfileConfigured(unittest.TestCase):
    @mock.patch("src.python.aws._aws_profile", return_value="default")
    @mock.patch("src.python.aws._aws_cli_get")
    def test_sso_session_profile_configured(self, mock_cli_get, mock_profile):
        values = {
            "sso_account_id": "111122223333",
            "sso_role_name": "DeveloperAccess",
            "sso_session": "company-sso",
            "sso_start_url": "",
        }
        mock_cli_get.side_effect = lambda key, **kwargs: values[key]

        self.assertTrue(_aws_sso_profile_configured())

    @mock.patch("src.python.aws._aws_profile", return_value="default")
    @mock.patch("src.python.aws._aws_cli_get")
    def test_legacy_sso_profile_configured(self, mock_cli_get, mock_profile):
        values = {
            "sso_account_id": "111122223333",
            "sso_role_name": "DeveloperAccess",
            "sso_session": "",
            "sso_start_url": "https://identitycenter.amazonaws.com/ssoins-example",
        }
        mock_cli_get.side_effect = lambda key, **kwargs: values[key]

        self.assertTrue(_aws_sso_profile_configured())

    @mock.patch("src.python.aws._aws_profile", return_value="default")
    @mock.patch("src.python.aws._aws_cli_get")
    def test_missing_account_is_not_configured(self, mock_cli_get, mock_profile):
        values = {
            "sso_account_id": "",
            "sso_role_name": "DeveloperAccess",
            "sso_session": "company-sso",
            "sso_start_url": "",
        }
        mock_cli_get.side_effect = lambda key, **kwargs: values[key]

        self.assertFalse(_aws_sso_profile_configured())


class Test_AwsUseDeviceCode(unittest.TestCase):
    def test_default_is_device_code(self):
        env = dict(os.environ)
        env.pop("AWS_SSO_USE_DEVICE_CODE", None)
        with mock.patch.dict(os.environ, env, clear=True):
            self.assertTrue(_aws_use_device_code())

    def test_disabled_values(self):
        for val in ("0", "false", "no", "False", "NO", ""):
            with mock.patch.dict(
                os.environ, {"AWS_SSO_USE_DEVICE_CODE": val}, clear=False
            ):
                self.assertFalse(_aws_use_device_code(), msg=val)

    def test_enabled_values(self):
        for val in ("1", "true", "yes", "True"):
            with mock.patch.dict(
                os.environ, {"AWS_SSO_USE_DEVICE_CODE": val}, clear=False
            ):
                self.assertTrue(_aws_use_device_code(), msg=val)


class Test_AwsSsoLoginCommand(unittest.TestCase):
    @mock.patch("src.python.aws.Path")
    @mock.patch("src.python.aws._aws_sso_profile_configured", return_value=True)
    @mock.patch("src.python.aws._aws_profile", return_value="default")
    @mock.patch("src.python.aws.shell_command")
    def test_login_uses_device_code_by_default(self, mock_shell, *_):
        env = dict(os.environ)
        env.pop("AWS_SSO_USE_DEVICE_CODE", None)
        with mock.patch.dict(os.environ, env, clear=True):
            _aws_sso_login()
        cmd = mock_shell.call_args.args[0]
        self.assertIn("aws sso login", cmd)
        self.assertIn("--use-device-code", cmd)

    @mock.patch("src.python.aws.Path")
    @mock.patch("src.python.aws._aws_sso_profile_configured", return_value=True)
    @mock.patch("src.python.aws._aws_profile", return_value="default")
    @mock.patch("src.python.aws.shell_command")
    def test_login_browser_flow_when_disabled(self, mock_shell, *_):
        with mock.patch.dict(
            os.environ, {"AWS_SSO_USE_DEVICE_CODE": "0"}, clear=False
        ):
            _aws_sso_login()
        cmd = mock_shell.call_args.args[0]
        self.assertIn("aws sso login", cmd)
        self.assertNotIn("--use-device-code", cmd)

    @mock.patch("src.python.aws.Path")
    @mock.patch("src.python.aws._aws_sso_profile_configured", return_value=False)
    @mock.patch("src.python.aws._aws_profile", return_value="default")
    @mock.patch("src.python.aws.shell_command")
    def test_configure_sso_uses_device_code_by_default(self, mock_shell, *_):
        env = dict(os.environ)
        env.pop("AWS_SSO_USE_DEVICE_CODE", None)
        with mock.patch.dict(os.environ, env, clear=True):
            _aws_sso_login()
        cmd = mock_shell.call_args.args[0]
        self.assertIn("aws configure sso", cmd)
        self.assertIn("--use-device-code", cmd)


class _FakeResult:
    def __init__(self, returncode=0, stdout=b"", stderr=b""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


class Test_SecretsNotEchoed(unittest.TestCase):
    @mock.patch("src.python.aws.shell_command")
    def test_aws_cli_set_does_not_echo_value(self, mock_shell):
        mock_shell.return_value = _FakeResult()

        buf = io.StringIO()
        with redirect_stdout(buf):
            aws_cli_set("aws_secret_access_key", "topsecretvalue", verbose=True)

        output = buf.getvalue()
        self.assertNotIn("topsecretvalue", output)
        # The generic runner must be invoked with verbose disabled so it does
        # not echo the command (which contains the secret value).
        self.assertFalse(mock_shell.call_args.kwargs.get("verbose", False))

    @mock.patch("src.python.aws.aws_cli_set")
    @mock.patch("src.python.aws.shell_command")
    def test_export_credentials_does_not_echo_secrets(self, mock_shell, mock_set):
        payload = {
            "AccessKeyId": "ASIAEXAMPLE",
            "SecretAccessKey": "secretkeyvalue",
            "SessionToken": "sessiontokenvalue",
        }
        mock_shell.return_value = _FakeResult(stdout=json.dumps(payload).encode())

        buf = io.StringIO()
        with redirect_stdout(buf):
            result = _aws_export_credentials(verbose=True)

        output = buf.getvalue()
        self.assertTrue(result)
        self.assertNotIn("secretkeyvalue", output)
        self.assertNotIn("sessiontokenvalue", output)
        # export-credentials returns secrets on stdout, so it must run with
        # verbose disabled to avoid the generic runner echoing them.
        self.assertFalse(mock_shell.call_args.kwargs.get("verbose", False))


if __name__ == "__main__":
    unittest.main()
