#!/usr/bin/env python3

import unittest

from src.python.utils import (
    format_cloud_name,
    format_instance_role,
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


if __name__ == "__main__":
    unittest.main()
