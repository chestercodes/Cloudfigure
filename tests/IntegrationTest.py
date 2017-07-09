import unittest
import cloudfigure as cf
from unittest import mock
import os, json
from os import listdir
from os.path import isfile, join

class MockCfn:
    def __init__(self, directory_path):
        self.calls = {}
        describe_files = [f for f in listdir(directory_path) if f.startswith("DescribeStack_")]
        for file_name in describe_files:
            name = file_name[len("DescribeStack_"):(len(file_name) - len(".json"))]
            self.calls[name] = json.loads(cf.read_all_text(join(directory_path, file_name)))
    
    def describe_stacks(self, StackName):
        if not StackName in self.calls:
            raise Exception("Doesnt exist")
        return self.calls[StackName]

class MockKms:
    def __init__(self, directory_path):
        kms_calls_text = cf.read_all_text(os.path.join(directory_path, "KmsCalls.json"))
        self.calls = json.loads(kms_calls_text)
        for call_key in self.calls.keys():
            to_change = self.calls[call_key]["Plaintext"]
            self.calls[call_key]["Plaintext"] = to_change.encode("utf-8")

    
    def decrypt(self, CiphertextBlob):
        blob = CiphertextBlob.decode("utf-8")
        if not blob in self.calls:
            raise Exception("Doesnt exist")
        return self.calls[blob]

class MockBoto:
    def __init__(self, kms, cfn):
        self.kms = kms
        self.cfn = cfn

    def client(self, service):
        if service == "cloudformation":
            return self.cfn
        if service == "kms":
            return self.kms
        raise Exception("shouldn't be asking for this")

class IntegrationTest(unittest.TestCase):
    def __init__(self, directory_path):
        self.working_dir = directory_path
        self.cfn = MockCfn(directory_path)
        self.kms = MockKms(directory_path)
        stack_ids_text = cf.read_all_text(os.path.join(directory_path, "StackIds.json"))
        self.stack_ids = json.loads(stack_ids_text)
        config_path = os.path.join(directory_path, "Cloudfigure.json")
        self.cloudfigure_config = cf.read_all_text(config_path)

        # assert against substituted files
        expected_files = {}
        expected_files_in_dir = [f for f in listdir(directory_path) if f.startswith("ExpectedFile_")]
        for file_name in expected_files_in_dir:
            name = file_name[len("ExpectedFile_"):]
            path = join(directory_path, name)
            expected_files[path] = cf.read_all_text(join(directory_path, file_name))
        self.expected_files = expected_files

        self.writes = {}
        cf.write_all_text = self.mock_write_all_text

        super().__init__()

    def mock_write_all_text(self, path, content):
        self.writes[path] = content

    def run(self):
        self.result = cf.run_cloudfigure(MockBoto(self.kms, self.cfn), self.cloudfigure_config, self.stack_ids, self.working_dir)
        return self.result

    def assert_expected_files(self):
        for expected_write in self.expected_files.keys():
            if expected_write not in self.writes:
                self.assertFalse(True, "file was written to which was not expected " + expected_write)
            actual = self.writes[expected_write]
            expected = self.expected_files[expected_write]
            self.assertEqual(actual, expected)


