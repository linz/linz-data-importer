"""
/***************************************************************************
 LINZ Data Importer
                                 A QGIS plugin
 Import LINZ (and others) OGC Datasets into QGIS
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
import ast
import os
import shutil
import re
import glob

from qgis.PyQt.QtTest import QTest
from qgis.PyQt.QtCore import Qt, QSettings
from qgis.utils import plugins
from qgis.core import QgsProject, QgsApplication
import xml.etree.ElementTree as ET

WAIT=1000

# Using 3 env vars as issue with travis
# when the 3 are supplied as json obj
API_KEYS={'data.linz.govt.nz':os.getenv('LDI_LINZ_KEY', None),
          'data.mfe.govt.nz': os.getenv('LDI_MFE_KEY', None),
          'geodata.nzdf.mil.nz':os.getenv('LDI_NZDF_KEY', None)}

TEST_CONF={'wmts':'Chart NZ 632 Banks Peninsula',
           'wfs':'NZ Railway Centrelines (Topo, 1:250k)'
           }


class UserWorkFlows(unittest.TestCase):
    """
    Testr user work flows to import data via the plugin
    """

    @classmethod
    def setUpClass(cls):
        """
        Set up at TestCase init
        """

        # Get the test executors current key so that 
        # We can revert back to when tests are complete
        cls.testers_keys = QSettings().value('linz_data_importer/apikeys')

    @classmethod
    def tearDownClass(cls):
        """
        Clean up at TestCase teardown
        """

        # Runs at TestCase teardown.
        QSettings().setValue('linz_data_importer/apikeys', cls.testers_keys)

    def setUp(self):
        """
        Runs before each test
        """

        self.ldi=plugins.get('linz-data-importer')
        self.ldi.services_loaded=False 

        domain='data.linz.govt.nz'
        self.api_key_instance = self.ldi.api_key_instance
        self.api_key_instance.setApiKeys({domain:API_KEYS[domain]})

        self.ldi.selected_crs='ESPG:2193'
        self.ldi.selected_crs_int=2193

        # Run
        self.ldi.actions[0].trigger()

    def tearDown(self):
        """
        Runs after each test
        """

        QTest.qWait(WAIT) # Just because I want to watch it open a close
        self.ldi.dlg.uTextFilter.setText('')
        self.ldi.dlg.close()
        QgsProject.instance().removeAllMapLayers()
        self.services_loaded=False
        item = self.ldi.dlg.uListOptions.findItems('ALL', Qt.MatchFixedString)[0]
        self.ldi.dlg.uListOptions.itemClicked.emit(item)

    def test_wfs_import(self):
        """
        Test display, filtering, selection and importing of WFS data 
        """
 
        self.import_service('wfs')

    def test_wmts_import(self):
        """
        Test display, filtering, selection and importing of WFS data 
        """

        self.import_service('wmts')

    def import_service(self, service):
        """
        Executes tests for all "test_w<x>s_import" methods
        """

        # Select WxS table view
        item = self.ldi.dlg.uListOptions.findItems(service.upper(), Qt.MatchFixedString)[0]
        self.ldi.dlg.uListOptions.itemClicked.emit(item)

        # Test the tableview widget is current stackedWidget
        self.assertEqual(self.ldi.dlg.uStackedWidget.currentIndex(), 0)

        # Test there is data
        self.assertNotEqual(self.ldi.table_model.rowCount(None), 0)

        # Ensure all records are of the selected type
        data_types=set([self.ldi.proxy_model.index(row, 2).data() 
                       for row in range(self.ldi.proxy_model.rowCount())])
        self.assertEqual(len(data_types),1)
        self.assertEqual(service.upper(), list(data_types)[0])

        # Filter
        self.ldi.dlg.uTextFilter.setText(TEST_CONF[service])
        QTest.qWait(WAIT)

        # Import the first row
        self.ldi.dlg.uTableView.selectRow(0)
        self.ldi.dlg.uBtnImport.clicked.emit(True)

        # Test the LayerRegistry to ensure the layer has been imported
        names = [layer.name() for layer in QgsProject.instance().mapLayers().values()]
        self.assertEqual(TEST_CONF[service], names[0])

    def test_all_services(self):
        """
        Test all services are shown in table 
        """

        # Set up 
        item = self.ldi.dlg.uListOptions.findItems('ALL', Qt.MatchFixedString)[0]
        self.ldi.dlg.uListOptions.itemClicked.emit(item)
        # Tests
        # Test there is data
        self.assertNotEqual(self.ldi.table_model.rowCount(None), 0)
        # ensure all services are are present in the table
        data_types=set([self.ldi.proxy_model.index(row, 2).data() 
                       for row in range(self.ldi.proxy_model.rowCount())])
        self.assertEqual(len(data_types),3)
        self.assertEqual(sorted([u'WFS', u'WMTS']), 
                         sorted(list(data_types)))


    def test_crs_combo_filter(self):
        """
        Test the importing of WMS layers into QGIS
        """

        #set text
        self.ldi.dlg.uCRSCombo.lineEdit().setText('ESPG:2193')
        #check that the lineEdit set the correct item in combobox
        self.assertEqual('ESPG:2193', self.ldi.dlg.uCRSCombo.currentText())
        
# def suite():
#     suite = unittest.TestSuite()
#     suite.addTests(unittest.makeSuite(ApiKeyTest, 'test'))
#     return suite
# 
# def run_tests():
#     unittest.TextTestRunner(verbosity=3).run(suite())
