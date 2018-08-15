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

import os
import unittest
from PyQt4.QtTest import QTest
from qgis.PyQt.QtCore import Qt, QSettings
from qgis.utils import plugins

API_KEY=(os.getenv('LDS_API', None))
WAIT=1000

class ApiKeyTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Runs at TestCase init."""
        cls.lds_plugin = plugins.get('ldsplugin')
        #cls.lds_plugin.all_services = ['loadWFS'] # Hack to make tests faster

    @classmethod
    def tearDownClass(cls):
        # Runs at TestCase teardown.
        #cls.lds_plugin.all_services = ['loadWMTS', 'loadWMS', 'loadWFS'] # Revert hack
        QSettings().setValue('ldsplugin/apikey', API_KEY)

    def setUp(self):
        """Runs before each test."""
        self.lds_plugin = plugins.get('ldsplugin')
        self.lds_plugin.actions[0].trigger()
        QTest.qWait(WAIT)

    def tearDown(self):
        """Runs after each test"""
        QTest.qWait(WAIT)
        self.lds_plugin.service_dlg.close()

    def test_temp(self): # TEMP
        self.assertEqual(1,1)

    def test_no_key(self):
        #Setup 
        item = self.lds_plugin.service_dlg.uListOptions.findItems('Settings', Qt.MatchFixedString)[0]
        self.lds_plugin.service_dlg.uListOptions.itemClicked.emit(item)
        self.lds_plugin.service_dlg.uTextAPIKey.setText('')
        QTest.qWait(WAIT)
        self.lds_plugin.service_dlg.uBtnSaveApiKey.clicked.emit(True)
        #Tests
        self.assertTrue(self.lds_plugin.service_dlg.uLabelWarning.isVisible())
        warning = self.lds_plugin.service_dlg.uLabelWarning.text()
        self.assertEqual(warning, 'Error: LDS API key must be provided - see settings')
 
    def test_set_unauthorized_key(self):
        #Setup
        item = self.lds_plugin.service_dlg.uListOptions.findItems('Settings', Qt.MatchFixedString)[0]
        self.lds_plugin.service_dlg.uListOptions.itemClicked.emit(item)
        self.lds_plugin.service_dlg.uTextAPIKey.setText('blahblahblah')
        QTest.qWait(WAIT)
        self.lds_plugin.service_dlg.uBtnSaveApiKey.clicked.emit(True)
        # Tests
        self.assertTrue(self.lds_plugin.service_dlg.uLabelWarning.isVisible())
        warning = self.lds_plugin.service_dlg.uLabelWarning.text()
        self.assertEqual(warning, 'Error: Unauthorized')

    def test_set_authorized_key(self):
        ''' Test executer must must have envi var = LDS_API set '''
        #Setup
        item = self.lds_plugin.service_dlg.uListOptions.findItems('Settings', Qt.MatchFixedString)[0]
        self.lds_plugin.service_dlg.uListOptions.itemClicked.emit(item)
        self.lds_plugin.service_dlg.uTextAPIKey.setText(API_KEY)
        QTest.qWait(WAIT)
        self.lds_plugin.service_dlg.uBtnSaveApiKey.clicked.emit(True)
        # Tests
        self.assertIsNotNone(API_KEY, 'LDS_API envi var not set')
        self.assertFalse(self.lds_plugin.service_dlg.uLabelWarning.isVisible())
        # Data has loaded with correct key? 
        self.assertNotEqual(self.lds_plugin.table_model.rowCount(None), 0)

def suite():
    suite = unittest.TestSuite()
    suite.addTests(unittest.makeSuite(ApiKeyTest, 'test'))
    return suite
 
def run_tests():
    unittest.TextTestRunner(verbosity=3).run(suite())
