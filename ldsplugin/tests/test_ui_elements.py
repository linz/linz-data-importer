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
from qgis.utils import plugins

WAIT=1000

class UiTest(unittest.TestCase):

    def setUp(self):
        """Runs before each test."""
        self.lds_plugin = plugins.get('ldsplugin')
        self.lds_plugin.actions[0].trigger()

    def tearDown(self):
        """Runs after each test"""
        QTest.qWait(WAIT) # Just because I want to watch it open a close
        self.lds_plugin.service_dlg.close()

    def test_service_dialog_is_active(self):
        self.assertTrue(self.lds_plugin.service_dlg.isVisible())

    def test_sw_tableview_is_default(self):
        """ The table view should be the first
        stack widget shown when plugin opened """
        self.assertEqual(self.lds_plugin.service_dlg.qStackedWidget.currentIndex(),0)

    def test_listItem_about_shows_widget_swSettings(self):
        """ The table view should be the first
        stack widget shown when plugin opened """
        item = self.lds_plugin.service_dlg.uListOptions.findItems('Settings', Qt.MatchFixedString)[0]
        self.lds_plugin.service_dlg.uListOptions.itemClicked.emit(item)
        self.assertEqual(self.lds_plugin.service_dlg.qStackedWidget.currentIndex(),1)

    def test_listItem_all_shows_widget_swTableView(self):
        """ The table view should be the first
        stack widget shown when plugin opened """
        item = self.lds_plugin.service_dlg.uListOptions.findItems('ALL', Qt.MatchFixedString)[0]
        self.lds_plugin.service_dlg.uListOptions.itemClicked.emit(item)
        self.assertEqual(self.lds_plugin.service_dlg.qStackedWidget.currentIndex(),0)

    def test_listItem_about_shows_widget_swAbout(self):
        """  """
        item = self.lds_plugin.service_dlg.uListOptions.findItems('About', Qt.MatchFixedString)[0]
        self.lds_plugin.service_dlg.uListOptions.itemClicked.emit(item)
        self.assertEqual(self.lds_plugin.service_dlg.qStackedWidget.currentIndex(),2)
 
    def test_listItem_wmts_shows_widget_swTableView(self):
        """  """
        item = self.lds_plugin.service_dlg.uListOptions.findItems('WMTS', Qt.MatchFixedString)[0]
        self.lds_plugin.service_dlg.uListOptions.itemClicked.emit(item)
        self.assertEqual(self.lds_plugin.service_dlg.qStackedWidget.currentIndex(),0)

    def test_listItem_wfs_shows_widget_swTableView(self):
        """  """
        item = self.lds_plugin.service_dlg.uListOptions.findItems('WFS', Qt.MatchFixedString)[0]
        self.lds_plugin.service_dlg.uListOptions.itemClicked.emit(item)
        self.assertEqual(self.lds_plugin.service_dlg.qStackedWidget.currentIndex(),0)

    def test_listItem_wms_shows_widget_swTableView(self):
        """  """
        item = self.lds_plugin.service_dlg.uListOptions.findItems('WMS', Qt.MatchFixedString)[0]
        self.lds_plugin.service_dlg.uListOptions.itemClicked.emit(item)
        self.assertEqual(self.lds_plugin.service_dlg.qStackedWidget.currentIndex(),0)

def suite():
    suite = unittest.TestSuite()
    suite.addTests(unittest.makeSuite(UiTest, 'test'))
    return suite
 
def run_tests():
    unittest.TextTestRunner(verbosity=3).run(suite())
