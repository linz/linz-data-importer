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
from PyQt4.QtTest import QTest
from qgis.PyQt.QtCore import Qt
from qgis.utils import plugins
from qgis.core import QgsMapLayerRegistry

WAIT=1000
TEST_CONF={'wms':'Chart NZ 252 Lake Wakatipu',
           'wmts':'Chart NZ 632 Banks Peninsula',
           'wfs':'NZ Railway Centrelines (Topo, 1:250k)'
           }

class UiTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Runs at TestCase init."""
        cls.lds_plugin = plugins.get('ldsplugin')

    def setUp(self):
        """Runs before each test."""
        self.lds_plugin = plugins.get('ldsplugin')
        self.lds_plugin.actions[0].trigger()

    def tearDown(self):
        """Runs after each test"""
        QTest.qWait(WAIT) # Just because I want to watch it open a close
        self.lds_plugin.service_dlg.uTextFilter.setText('')
        self.lds_plugin.service_dlg.close()
        QgsMapLayerRegistry.instance().removeAllMapLayers()

    def test_wfs_import(self):
        self.import_service('wfs')

    def test_wms_import(self):
        self.import_service('wms')

    def test_wmts_import(self):
        self.import_service('wmts')

    def import_service(self, service):
        ''' rather than writing the same tests for
        all service imports they are all executed
        via this method '''
        # Select wmts table view
        item = self.lds_plugin.service_dlg.uListOptions.findItems(service.upper(), Qt.MatchFixedString)[0]
        self.lds_plugin.service_dlg.uListOptions.itemClicked.emit(item)
        # Test the tableview widget is current stackedWidget
        self.assertEqual(self.lds_plugin.service_dlg.qStackedWidget.currentIndex(), 0)
        # Test there is data
        self.assertNotEqual(self.lds_plugin.table_model.rowCount(None), 0)
        # ensure all records are of the selected type
        data_types=set([self.lds_plugin.proxy_model.index(row, 2).data() 
                       for row in xrange(self.lds_plugin.proxy_model.rowCount())])
        self.assertEqual(len(data_types),1)
        self.assertEqual(service.upper(), list(data_types)[0])
        #Filter
        self.lds_plugin.service_dlg.uTextFilter.setText(TEST_CONF[service].replace('(', '\(').replace(')','\)'))
        QTest.qWait(WAIT)
        #Import the first row
        # TODO this should be via 'click' signal
        self.lds_plugin.service_dlg.uDatasetsTableView.selectRow(0)
        self.lds_plugin.service_dlg.uBtnImport.clicked.emit(True)
        # Test the LayerRegistry to ensure the layer has been imported
        names = [layer.name() for layer in QgsMapLayerRegistry.instance().mapLayers().values()]
        self.assertEqual(TEST_CONF[service], names[0]) # The one layer loaded in this test is of the expected names

    def test_all_services(self):
        ''' Test all services shown in table '''
        # Set up 
        item = self.lds_plugin.service_dlg.uListOptions.findItems('ALL', Qt.MatchFixedString)[0]
        self.lds_plugin.service_dlg.uListOptions.itemClicked.emit(item)
        # Tests
        # Test there is data
        self.assertNotEqual(self.lds_plugin.table_model.rowCount(None), 0)
        # ensure all services are are present in the table
        data_types=set([self.lds_plugin.proxy_model.index(row, 2).data() 
                       for row in xrange(self.lds_plugin.proxy_model.rowCount())])
        self.assertEqual(len(data_types),3)
        self.assertEqual([u'WMS', u'WFS', u'WMTS'], list(data_types))

def suite():
    suite = unittest.TestSuite()
    suite.addTests(unittest.makeSuite(UiTest, 'test'))
    return suite

def run_tests():
    unittest.TextTestRunner(verbosity=3).run(suite())

