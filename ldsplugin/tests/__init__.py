# -*- coding: utf-8 -*-

import sys
import unittest

from test_script_assistant import ScriptAssistantSettingsTest


def run_tests():
    suite = unittest.TestSuite()
    suite.addTests(unittest.makeSuite(ScriptAssistantSettingsTest, "test"))
    unittest.TextTestRunner(verbosity=2, stream=sys.stdout).run(suite)