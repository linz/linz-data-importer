import os
import sys
import unittest

__location__ = os.path.dirname(os.path.realpath(__file__))

def run_test_modules():
    """
    Loops through all TestCase instances in a test folder to find
    unique test modules
    """
    test_suite = unittest.TestLoader().discover(__location__, pattern="test_*.py")
    unittest.TextTestRunner(verbosity=3, stream=sys.stdout).run(test_suite)
