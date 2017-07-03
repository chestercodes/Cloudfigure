import unittest
import os
import cloudfigure
from tests import IntegrationTest
from unittest import mock

script_path = os.path.realpath(__file__)
script_dir = os.path.dirname(script_path)
int_tests_dir = os.path.abspath(os.path.join(script_dir, "../integration-tests"))

class IntegrationTests(unittest.TestCase):
    def test_that_ParentAndChildStacks_passes(self):
        test_dir = os.path.join(int_tests_dir, "ParentAndChildStacks")
        int_test = IntegrationTest.IntegrationTest(test_dir)

        result = int_test.run()

        int_test.assert_expected_files()

if __name__ == "__main__":
    unittest.main()
