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
    ],
    "ValueToFile": [
      {"Name": "SomeAddress", "Path": "./SomeValue.txt"}
    ]
}"""

        result = cloudfigure.parse_cloudfigure_file(config)

        self.assertTrue(result[0])
        config = result[1]
        self.assertEqual(len(config.configuration), 2)
        self.assertEqual(config.configuration[0].name, "SomeAddress")
        self.assertEqual(config.configuration[0].location, "SomeEndpoint")
        self.assertEqual(config.configuration[0].unencrypt, False)

        self.assertEqual(config.configuration[1].name, "SomePassword")
        self.assertEqual(config.configuration[1].location, "SomeOutputName")
        self.assertEqual(config.configuration[1].unencrypt, True)

        self.assertEqual(len(config.substitute_into), 1)
        self.assertEqual(config.substitute_into[0], "./SomePath.txt")

        self.assertEqual(len(config.value_to_file), 1)
        self.assertEqual(config.value_to_file[0].name, "SomeAddress")
        self.assertEqual(config.value_to_file[0].path, "./SomeValue.txt")

    def test_that_junk_json_doesnt_throw_and_returns_false_and_None(self):
        config = """dfiwu9e7b3rc08n8b9sc__+$F£9"""

        result = cloudfigure.parse_cloudfigure_file(config)

        self.assertFalse(result[0])
        self.assertEqual(result[1], None)


if __name__ == "__main__":
    unittest.main()
