#!/usr/bin/env python3

import unittest

import click

from src.python.deploy_command import DeployCommand


class Test_DeploymentNameCallback(unittest.TestCase):
    def test_valid_names(self):
        for name in ["a", "abc", "abc-123", "0", "x" * 32]:
            self.assertEqual(DeployCommand.deployment_name_callback(None, None, name), name)

    def test_uppercase_rejected(self):
        with self.assertRaises(click.BadParameter):
            DeployCommand.deployment_name_callback(None, None, "ABC")

    def test_underscore_rejected(self):
        with self.assertRaises(click.BadParameter):
            DeployCommand.deployment_name_callback(None, None, "abc_def")

    def test_empty_rejected(self):
        with self.assertRaises(click.BadParameter):
            DeployCommand.deployment_name_callback(None, None, "")

    def test_too_long_rejected(self):
        with self.assertRaises(click.BadParameter):
            DeployCommand.deployment_name_callback(None, None, "x" * 33)


class Test_IngressCidrsCallback(unittest.TestCase):
    def test_none_returns_none(self):
        self.assertIsNone(DeployCommand.ingress_cidrs_callback(None, None, None))

    def test_empty_returns_empty(self):
        self.assertEqual(DeployCommand.ingress_cidrs_callback(None, None, ""), "")

    def test_special_values(self):
        for value in ["auto", "myip", "myip/8", "myip/16", "myip/24", "mynet", "nvidia"]:
            self.assertEqual(
                DeployCommand.ingress_cidrs_callback(None, None, value),
                value,
            )

    def test_valid_cidr(self):
        self.assertEqual(
            DeployCommand.ingress_cidrs_callback(None, None, "10.0.0.0/16"),
            "10.0.0.0/16",
        )

    def test_multiple_values(self):
        self.assertEqual(
            DeployCommand.ingress_cidrs_callback(None, None, "myip, 10.0.0.0/8"),
            "myip,10.0.0.0/8",
        )

    def test_invalid_cidr_rejected(self):
        with self.assertRaises(click.BadParameter):
            DeployCommand.ingress_cidrs_callback(None, None, "not-a-cidr")

    def test_case_normalized(self):
        self.assertEqual(
            DeployCommand.ingress_cidrs_callback(None, None, "MyIP"),
            "myip",
        )


if __name__ == "__main__":
    unittest.main()
