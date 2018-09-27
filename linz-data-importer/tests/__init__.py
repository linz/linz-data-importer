import sys
import unittest

from test_ldi_plugin import UnitLevel
from test_ldi_ui_elements import  UiTest
from test_ldi_integration import CorruptXml, UserWorkFlows

def run_tests():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(UnitLevel))
    unittest.TextTestRunner(verbosity=2, stream=sys.stdout).run(suite)