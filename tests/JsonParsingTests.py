import unittest
import cloudfigure
from unittest import mock

class JsonParsingTests(unittest.TestCase):
    def test_that_valid_json_parses(self):
        config = """{
    "Configuration": [
            {"Name": "SomeAddress",  "Location": "SomeEndpoint"},
            {"Name": "SomePassword", "Location": "SomeOutputName", "Unencrypt": true}
    ],
    "SubstituteInto": [
        "./SomePath.txt"
    ]
}"""

        result = cloudfigure.parse_cloudfigure_file(config)

        self.assertEqual(len(result.configuration), 2)
        self.assertEqual(result.configuration[0].name, "SomeAddress")
        self.assertEqual(result.configuration[0].location, "SomeEndpoint")
        self.assertEqual(result.configuration[0].unencrypt, False)

        self.assertEqual(result.configuration[1].name, "SomePassword")
        self.assertEqual(result.configuration[1].location, "SomeOutputName")
        self.assertEqual(result.configuration[1].unencrypt, True)

        self.assertEqual(len(result.substitute_into), 1)
        self.assertEqual(result.substitute_into[0], "./SomePath.txt")


if __name__ == "__main__":
    unittest.main()
