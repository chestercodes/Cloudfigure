import boto3
import argparse
import os
import sys
import json
import base64

is_running_as_script = __name__ == "__main__"

def file_exists(path):
    return os.path.exists(path)

def read_all_text(path):
    with open(path, 'r') as myfile:
        data = myfile.read().replace('\n', '')
    return data

def write_all_text(path, content):
    pass

class ValueToFile:
    def __init__(self, name, path):
        self.name = name
        self.path = path

class ConfigValue:
    def __init__(self, name, location, unencrypt):
        self.name = name
        self.location = location
        self.unencrypt = unencrypt

        if len(self.location.split('.')) > 2:
            print("Error with config location - " + location)
            print("Error - sorry, we can only handle child parent relations, no grand kids allowed.")
            sys.exit(1)

    def is_not_in_parent(self):
        return len(self.location.split('.')) > 1

    def child_location_or_none(self):
        if not self.is_not_in_parent():
            return None
        return self.location.split('.')[0]
    def location_in_stack(self):
        if not self.is_not_in_parent():
            return self.location
        return self.location.split('.')[1]


class CloudfigureFile:
    def __init__(self):
        self.configuration = []
        self.substitute_into = []
        self.value_to_file = []
    def add_config_value(self, config_value):
        self.configuration.append(config_value)
    def add_substitute_into(self, substitute_into):
        self.substitute_into.append(substitute_into)
    def add_value_to_file(self, value_to_file):
        self.value_to_file.append(value_to_file)

    def output_values(self, cloudfigure_values, working_dir):
        for substitute_into_file in self.substitute_into:
            if os.path.isabs(substitute_into_file):
                path = substitute_into_file
            else:
                path = os.path.join(working_dir, substitute_into_file)
                path = os.path.realpath(path)
            if os.path.exists(path) is False:
                print("Error - fila doesnt exist at - " + path)
                sys.exit(1)
            file_contents = read_all_text(path)
            for value_key in cloudfigure_values.keys():
                value = cloudfigure_values[value_key]
                placeholder = "#{" + value_key + "}"
                file_contents = file_contents.replace(placeholder, value)
            write_all_text(path, file_contents)

        for value_into_file in self.value_to_file:
            if os.path.isabs(value_into_file.path):
                path = value_into_file.path
            else:
                path = os.path.join(working_dir, value_into_file.path)
                path = os.path.realpath(path)
            value = cloudfigure_values[value_into_file.name]
            write_all_text(path, value)


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

        if 'SubstituteInto' in json_obj:
            for substitute_into in json_obj['SubstituteInto']:
                config.add_substitute_into(substitute_into)

        if 'ValueToFile' in json_obj:
            for value_to_file_obj in json_obj['ValueToFile']:
                if "Name" not in value_to_file_obj:
                    print("Error - Config not valid, missing Name property")
                    return (False, None)
                if "Path" not in value_to_file_obj:
                    print("Error - Config not valid, missing Path property")
                    return (False, None)
                value_to_file = ValueToFile(value_to_file_obj["Name"], value_to_file_obj["Path"])
                config.add_value_to_file(value_to_file)

        return (True, config)
    except ValueError:
        print("Error - Failed read cloudfigure json file")
        return (False, None)

def get_outputs_from_stack_id(cfn, stack_id):
    response = cfn.describe_stacks(StackName=stack_id)
    stack = response["Stacks"][0]
    outputs = {}
    for output in stack["Outputs"]:
        outputs[output["OutputKey"]] = output["OutputValue"]
    return outputs

def unencrypt(kms, val):
    decoded = base64.b64decode(val)
    decrypted = kms.decrypt(CiphertextBlob=decoded)
    plaintext_bytes = decrypted['Plaintext']
    plaintext = plaintext_bytes.decode("utf-8")
    return plaintext

def run_cloudfigure(boto, cloudfigure_config, stack_ids, working_dir, assume_role=None, verbose=False):
    print("Running Cloudfigure.")

    (parse_successful, cloudfigure_file) = parse_cloudfigure_file(cloudfigure_config)
    if parse_successful is False:
        print("Error - cloudfigure file is not parseable")
        sys.exit(1)

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

    child_logical_id_to_stack_id = {}

    # complete the stacks info retrieval
    for config_value in cloudfigure_file.configuration:
        if config_value.is_not_in_parent():
            config_value_is_in_a_parent_stack = False
            child_stack_logical_id = config_value.child_location_or_none()
            for parent_stack in stack_ids:
                parent_stacks_values = stack_id_and_outputs[parent_stack]
                if child_stack_logical_id in parent_stacks_values:
                    config_value_is_in_a_parent_stack = True
                    child_stack_id = parent_stacks_values[child_stack_logical_id]
            if config_value_is_in_a_parent_stack is False:
                print("Error - could not find child logical id in any of the stacks" + child_stack_logical_id)
                sys.exit(1)

            stack_id_and_outputs[child_stack_id] = get_outputs_from_stack_id(cfn, child_stack_id)
            child_logical_id_to_stack_id[child_stack_logical_id] = child_stack_id

    cloudfigure_values = {}

    # get values from stack
    for config_value in cloudfigure_file.configuration:
        if config_value.is_not_in_parent():
            child_stack_logical_id = config_value.child_location_or_none()
            child_stack_id = child_logical_id_to_stack_id[child_stack_logical_id]
            child_stack_values = stack_id_and_outputs[child_stack_id]
            location = config_value.location_in_stack()
            if location in child_stack_values:
                child_stack_location_value = child_stack_values[location]
                if config_value.unencrypt:
                    child_stack_location_value = unencrypt(kms, child_stack_location_value)
                cloudfigure_values[config_value.name] = child_stack_location_value
            else:
                print("Error - Location is not in child stack Location - " + config_value.location + " Stack - " + child_stack_id)
                sys.exit(1)
        else:
            is_in_parent_stack = False
            for parent_stack in stack_ids:
                stack_values = stack_id_and_outputs[parent_stack]
                if config_value.location in stack_values:
                    is_in_parent_stack = True
                    location_value = stack_values[config_value.location]
                    if config_value.unencrypt:
                        location_value = unencrypt(kms, location_value)
                    cloudfigure_values[config_value.name] = location_value
            if is_in_parent_stack is False:
                print("Error - cant find location in stack(s)" + config_value.location)

    cloudfigure_file.output_values(cloudfigure_values, working_dir)
    print("Finished cloudfigure")




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
                stack_ids = json.load(args.stack_ids_in_file)
            else:
                print("Error - file doesn't exist")
                sys.exit(1)
    else:
        stack_ids = args.stack_ids
        if verb: print("Stack id(s) are:")
        for stack_id in args.stack_ids:
            if verb: print(" - " + stack_id)

    run_cloudfigure(boto, cloudfigure_config, stack_ids, args.working_dir, args.assume_role, args.verbose)

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
    PARSER.add_argument('--working_dir', nargs='?', default=".")


    run_cloudfigure_script(boto3, PARSER.parse_args())
