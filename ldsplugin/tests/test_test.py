"""
/***************************************************************************
 QgisLdsPlugin
                                 A QGIS plugin
 Import LDS OGC Datasets into QGIS
                              -------------------
        begin                : 2018-04-07
        git sha              : $Format:%H$
        copyright            : (C) 2017 by Land Information New Zealand
        email                : splanzer@linz.govt.nz
 ***************************************************************************/
/***************************************************************************
 *   This program is released under the terms of the 3 clause BSD license. *
 *   see the LICENSE file for more information                             *
 ***************************************************************************/
"""

import unittest
from qgis.utils import plugins, active_plugins


class TestTest(unittest.TestCase):


    @classmethod
    def setUpClass(cls):
        """Runs at TestCase init."""
        cls.lds_plugin = plugins.get('ldsplugin')

    def setUp(self):
        """Runs before each test."""
        self.lds_plugin = plugins.get('ldsplugin')
        self.lds_plugin.actions[0].trigger()

    def test_temp1(self):
        self.assertEqual(1,1)

    def test_temp2(self):
        self.assertNotEqual(1,2)

    def test_temp3(self):
        self.assertTrue(True)

    def test_plugin_is_active(self):
        self.assertIn('ldsplugin', active_plugins) 

def suite():
    suite = unittest.TestSuite()
    suite.addTests(unittest.makeSuite(TestTest, 'test'))
    return suite
 
def run_tests():
    unittest.TextTestRunner(verbosity=3).run(suite())
