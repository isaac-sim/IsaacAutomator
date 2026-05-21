#!/usr/bin/env python3

import os
import unittest
from unittest import mock

from src.python.aws import _aws_env_credentials_set, aws_load_credentials


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


if __name__ == "__main__":
    unittest.main()
