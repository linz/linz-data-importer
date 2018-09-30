import sys
import unittest
import os

__location__ = os.path.dirname(os.path.realpath(__file__))


# from test_ldi_plugin import UnitLevel
# from test_ldi_ui_elements import  UiTest
# from test_ldi_integration import CorruptXml, UserWorkFlows
# 
# def run_tests():
#     suite = unittest.TestSuite()
#     test_suite = unittest.TestLoader().discover(__location__, pattern="test_*.py")
# 
#     #suite.addTest(unittest.makeSuite(UnitLevel))
#     suite.addTest(unittest.makeSuite(UserWorkFlows))
#     unittest.TextTestRunner(verbosity=2, stream=sys.stdout).run(suite)
def run_tests():

    test_suite = unittest.TestLoader().discover(__location__, pattern="test_ldi.*py")
    unittest.TextTestRunner(verbosity=2, stream=sys.stdout).run(test_suite)