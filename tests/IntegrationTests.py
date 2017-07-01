import unittest
import cloudfigure
from IntegrationTest import IntegrationTest
from unittest import mock

class IntegrationTests(unittest.TestCase):
    def test_that_ParentAndChildStacks_passes(self):
        int_test = IntegrationTest("../integration-tests/ParentAndChildStacks")

        result = int_test.run()

if __name__ == "__main__":
    unittest.main()
