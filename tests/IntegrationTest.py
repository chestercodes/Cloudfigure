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
    
    def describe_stacks(self, stack_id):
        if not stack_id in self.calls:
            raise Exception("Doesnt exist")
        return self.calls[stack_id]

class MockKms:
    def __init__(self, directory_path):
        kms_calls_text = cf.read_all_text(os.path.join(directory_path, "KmsCalls.json"))
        self.calls = json.loads(kms_calls_text)
    
    def decrypt(self, CiphertextBlob):
        if not CiphertextBlob in self.calls:
            raise Exception("Doesnt exist")
        return self.calls[CiphertextBlob]

class IntegrationTest:
    def __init__(self, directory_path):
        self.cfn = MockCfn(directory_path)
        self.kms = MockKms(directory_path)
        self.expected = cf.read_all_text(os.path.join(directory_path, "Expected"))
        stack_ids_text = cf.read_all_text(os.path.join(directory_path, "StackIds.json"))
        self.stack_ids = json.loads(stack_ids_text)
        config_path = os.path.join(directory_path, "Cloudfigure.json")
        self.cloudfigure_config = cf.read_all_text(config_path)
    
    def mock_client(self, service):
        if service == "cloudformation":
            return self.cfn
        if service == "kms":
            return self.kms
        raise Exception("shouldn't be asking for this")

    def run(self):
        self.result = cf.run_cloudfigure({"client": self.mock_client}, self.cloudfigure_config, self.stack_ids)
        return self.result

