import boto3
import argparse
import os
import sys
import json

is_running_as_script = __name__ == "__main__"

def file_exists(path):
    return os.path.exists(path)

def read_all_text(path):
    with open(path, 'r') as myfile:
        data = myfile.read().replace('\n', '')
    return data

def write_all_text(path, content):
    pass

class ConfigValue:
    def __init__(self, name, location, unencrypt):
        self.name = name
        self.location = location
        self.unencrypt = unencrypt

class CloudfigureFile:
    def __init__(self):
        self.configuration = []
        self.substitute_into = []
    def add_config_value(self, config_value):
        self.configuration.append(config_value)
    def add_substitute_into(self, substitute_into):
        self.substitute_into.append(substitute_into)

def parse_cloudfigure_file(config_json):
    try:
        config = CloudfigureFile()
        json_obj = json.loads(config_json)

        for config_value in json_obj['Configuration']:
            if "Name" not in config_value:
                print("Error - Config not valid, missing Name property")
                return (False, None)
            name = config_value["Name"]
            location = config_value["Location"]
            if "Location" not in config_value:
                print("Error - Config not valid, missing Location property")
                return (False, None)
            if "Unencrypt" in config_value:
                unencrypt = config_value["Unencrypt"]
            else:
                unencrypt = False
            config_val = ConfigValue(name, location, unencrypt)
            config.add_config_value(config_val)

        for substitute_into in json_obj['SubstituteInto']:
            config.add_substitute_into(substitute_into)

        return (True, config)
    except ValueError:
        print("Error - Failed read cloudfigure json file")
        return (False, None)

def get_outputs_from_stack_id(cfn, stack_id):
    response = cfn.describe_stacks(StackName=stack_id)
    stack = response["Stacks"][0]
    pause = 0

def run_cloudfigure(boto, cloudfigure_config, stack_ids, assume_role=None, verbose=False):
    print("Running Cloudfigure.")
    sts_role_or_none = None
    if assume_role is not None:
        if verbose: print("Try to assume role - " + assume_role)
        print("Assume IAM role - " + assume_role)
        sts = boto.client('sts')
        try:
            sts_role_or_none = sts.assume_role(RoleArn=assume_role, RoleSessionName="Cloudfigure")
        except Exception as e:
            print("Error - failed to assume role")
            print(e)
            sys.exit(1)
        print("Assumed role")

    if sts_role_or_none is None:
        kms = boto.client('kms')
        cfn = boto.client('cloudformation')
    else:
        credentials = sts_role_or_none['Credentials']
        kms = boto.client('kms',
            aws_access_key_id = credentials['AccessKeyId'],
            aws_secret_access_key = credentials['SecretAccessKey'],
            aws_session_token = credentials['SessionToken'])
        cfn = boto.client('cloudformation',
            aws_access_key_id = credentials['AccessKeyId'],
            aws_secret_access_key = credentials['SecretAccessKey'],
            aws_session_token = credentials['SessionToken'])

    stack_id_and_outputs = {}
    for s_id in stack_ids:
        outputs = get_outputs_from_stack_id(cfn, s_id)
        stack_id_and_outputs[s_id] = outputs

    write_all_text("some-path", "some-content")


def run_cloudfigure_script(boto, args):
    verb = args.verbose
    if args.assume_role != None:
        print("Assume role")
    else:
        if verb: print("Dont assume role")

    if verb: print("Cloudfigure file is located at: " + args.cloudfigure_file)
    if file_exists(args.cloudfigure_file):
        if verb: print("file exists.")
        cloudfigure_config = read_all_text(args.cloudfigure_file)
    else:
        print("Error - file doesn't exist at " + args.cloudfigure_file)
        sys.exit(1)

    if len(args.stack_ids) < 1:
        print("No stack ids specified in call, try look for them in file")
        if args.stack_ids_in_file is None:
            print("Error - please provide at least 1 stack id or specify file location")
            sys.exit(1)
        else:
            print("stack ids file is located at: " + args.stack_ids_in_file)
            if file_exists(args.stack_ids_in_file):
                if verb: print("file exists.")
            else:
                print("Error - file doesn't exist")
                sys.exit(1)
    else:
        stack_ids = args.stack_ids
        if verb: print("Stack id(s) are:")
        for stack_id in args.stack_ids:
            if verb: print(" - " + stack_id)

    run_cloudfigure(boto, cloudfigure_config, stack_ids, args.assume_role, args.verbose)

if is_running_as_script:
    # don't want to run if importing as module
    PARSER = argparse.ArgumentParser(description='arguments for cloudfigure')
    PARSER.add_argument('--assume_role', nargs='?',
                        help='Optionally assume IAM role to get config, enter full aws arn.')
    PARSER.add_argument('--cloudfigure_file', nargs='?', default='./Cloudfigure.json',
                        help='Specify cloudfigure file, defaults to ./Cloudfigure.json')
    PARSER.add_argument('--stack_ids', nargs='+', default=[], help='StackId(s) of initial stack')
    PARSER.add_argument('--stack_ids_in_file', nargs='?',
                        help='StackId(s) as a json array, in text file at specified location.')
    PARSER.add_argument('--verbose', '-v', action='store_true', help='log more stuff')

    run_cloudfigure_script(boto3, PARSER.parse_args())
