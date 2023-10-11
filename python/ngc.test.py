#!/usr/bin/env python3

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

import os
import unittest

from python.ngc import check_ngc_access


class Test_NGC_Key_Validation(unittest.TestCase):
    INVALID_KEY = "__invalid__"
    VALID_KEY = os.environ.get("NGC_API_KEY", "__none__")

    def test_invalid_key(self):
        """Test invalid key"""
        r = check_ngc_access(self.INVALID_KEY)
        self.assertEqual(r, 100)

    def test_valid_key(self):
        """Test valid key (should be set in NGC_API_KEY env var)"""

        if "__none__" == self.VALID_KEY:
            self.skipTest("No NGC_API_KEY env var set")
            return

        r = check_ngc_access(self.VALID_KEY)
        self.assertEqual(r, 0)


if __name__ == "__main__":
    unittest.main()
