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
import time
from PyQt4.QtTest import QTest
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import (QListWidget, QTableView, QLabel, QTextEdit,
                             QLineEdit, QPushButton, QListWidget)
from qgis.utils import plugins

WAIT=1000

class UiTest(unittest.TestCase):
    """
    Just test UI elements. No data requests
     
    """

    def setUp(self):
        """Runs before each test."""
        self.lds_plugin = plugins.get('ldsplugin')
        self.lds_plugin.actions[0].trigger()

    def tearDown(self):
        """Runs after each test"""
        QTest.qWait(WAIT) # Just because I want to watch it open a close
        self.lds_plugin.service_dlg.close()
        self.services_loaded=False

    def test_service_dialog_is_active(self):
        self.assertTrue(self.lds_plugin.service_dlg.isVisible())

    def test_elements_exist(self):
        """ Test all ui elements exist
        and are of the expected types  
        """
        self.assertEqual(type(self.lds_plugin.service_dlg.uListOptions), QListWidget)
        self.assertEqual(type(self.lds_plugin.service_dlg.uDatasetsTableView), QTableView)
        self.assertEqual(type(self.lds_plugin.service_dlg.uBtnImport), QPushButton)
        self.assertEqual(type(self.lds_plugin.service_dlg.uTextFilter), QLineEdit)
        self.assertEqual(type(self.lds_plugin.service_dlg.uTextDescription), QTextEdit)
        self.assertEqual(type(self.lds_plugin.service_dlg.uImagePreview), QLabel)
        self.assertEqual(type(self.lds_plugin.service_dlg.uLabelWarning), QLabel)

    def test_sw_tableview_is_default(self):
        """ The table view should be the first
        stack widget shown when plugin opened """
        self.assertEqual(self.lds_plugin.service_dlg.qStackedWidget.currentIndex(),0)

    def test_listItem_about_shows_widget_swSettings(self):
        """ Check the stacked widget index and sinals
        When 'Settings' is clicked - the stacked widgets current index
        should now be == 1 """
        item = self.lds_plugin.service_dlg.uListOptions.findItems('Settings', Qt.MatchFixedString)[0]
        self.lds_plugin.service_dlg.uListOptions.itemClicked.emit(item)
        self.assertEqual(self.lds_plugin.service_dlg.qStackedWidget.currentIndex(),1)

    def test_listItem_all_shows_widget_swTableView(self):
        """ Check the stacked widget index and sinals
        When 'All' is clicked - the stacked widgets current index
        should now be == 0 """
        item = self.lds_plugin.service_dlg.uListOptions.findItems('ALL', Qt.MatchFixedString)[0]
        self.lds_plugin.service_dlg.uListOptions.itemClicked.emit(item)
        self.assertEqual(self.lds_plugin.service_dlg.qStackedWidget.currentIndex(),0)

    def test_listItem_about_shows_widget_swAbout(self):
        """ Check the stacked widget index and sinals
        When 'All' is clicked - the stacked widgets current index
        should now be == 2 """
        item = self.lds_plugin.service_dlg.uListOptions.findItems('About', Qt.MatchFixedString)[0]
        self.lds_plugin.service_dlg.uListOptions.itemClicked.emit(item)
        self.assertEqual(self.lds_plugin.service_dlg.qStackedWidget.currentIndex(),2)
 
    def test_listItem_wmts_shows_widget_swTableView(self):
        """ Check the stacked widget index and sinals
        When 'WMTS' is clicked - the stacked widgets current index
        should now be == 0 """
        item = self.lds_plugin.service_dlg.uListOptions.findItems('WMTS', Qt.MatchFixedString)[0]
        self.lds_plugin.service_dlg.uListOptions.itemClicked.emit(item)
        self.assertEqual(self.lds_plugin.service_dlg.qStackedWidget.currentIndex(),0)

    def test_listItem_wfs_shows_widget_swTableView(self):
        """ Check the stacked widget index and sinals
        When 'WFS' is clicked - the stacked widgets current index
        should now be == 0 """
        item = self.lds_plugin.service_dlg.uListOptions.findItems('WFS', Qt.MatchFixedString)[0]
        self.lds_plugin.service_dlg.uListOptions.itemClicked.emit(item)
        self.assertEqual(self.lds_plugin.service_dlg.qStackedWidget.currentIndex(),0)

    def test_listItem_wms_shows_widget_swTableView(self):
        """ Check the stacked widget index and sinals
        When 'WMS' is clicked - the stacked widgets current index
        should now be == 0 """
        item = self.lds_plugin.service_dlg.uListOptions.findItems('WMS', Qt.MatchFixedString)[0]
        self.lds_plugin.service_dlg.uListOptions.itemClicked.emit(item)
        self.assertEqual(self.lds_plugin.service_dlg.qStackedWidget.currentIndex(),0)

def suite():
    suite = unittest.TestSuite()
    suite.addTests(unittest.makeSuite(UiTest, 'test'))
    return suite
 
def run_tests():
    unittest.TextTestRunner(verbosity=3).run(suite())
