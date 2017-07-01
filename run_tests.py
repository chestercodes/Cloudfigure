import pip
import os

def ensure_env_suitable():
    dir_path = os.path.dirname(os.path.realpath(__file__))
    req_path = os.path.join(dir_path, 'requirements.txt')
    pip.main(['install', '-r', req_path])

ensure_env_suitable()

# Need to run the test in a special way that TeamCity understands the output of.
# Therefore need the teamcity-messages to be in our environment
#from teamcity import is_running_under_teamcity
#from teamcity.unittestpy import TeamcityTestRunner
import unittest

# import the test modules
from tests import JsonParsingTests

if __name__ == '__main__':
    #if is_running_under_teamcity():
    #    runner = TeamcityTestRunner()
    #else:
    runner = unittest.TextTestRunner()

    # add modules to suite
    suite = unittest.defaultTestLoader.loadTestsFromModule(JsonParsingTests)
    #suite.addTests( unittest.defaultTestLoader.loadTestsFromModule(todo))
    runner.run(suite)
