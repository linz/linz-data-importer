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

WAIT = 1000

# Using 4 env vars as issue with travis
# when the 4 are supplied as json obj
API_KEYS = {
    "data.linz.govt.nz": os.getenv("LDI_LINZ_KEY", None),
    "data.mfe.govt.nz": os.getenv("LDI_MFE_KEY", None),
    "geodata.nzdf.mil.nz": os.getenv("LDI_NZDF_KEY", None),
    "basemaps.linz.govt.nz": os.getenv("LDI_BASEMAPS_KEY", None),
}


TEST_CONF = {
    "wmts": [
      "Chart NZ 632 Banks Peninsula",
      "aerial Whanganui urban 2017-18 0.075m",
    ],
    "wfs": [
      "NZ Railway Centrelines (Topo, 1:250k)",
    ]
}

class CorruptXml(unittest.TestCase):
    """
    Test methods for handling corrupt localstore
    """

    @classmethod
    def setUpClass(cls):
        """
        Set up at TestCase init
        """

        # Get the test executors current key so that
        # We can revert back to when tests are complete
        cls.testers_keys = QSettings().value("linz_data_importer/apikeys")
        # cls.ldi_plugin = plugins.get('linz-data-importer')

    @classmethod
    def tearDownClass(cls):
        """
        Clean up at TestCase teardown
        """

        QSettings().setValue("linz_data_importer/apikey", cls.testers_keys)

    def setUp(self):
        """
        Runs before each test
        """

        # Get reference to plugin
        self.ldi = plugins.get("linz-data-importer")

        # Dont run cache update
        self.ldi.services_loaded = False
        self.ldi.update_cache = False

        # Domain to run test against (lds only service with all WxS)
        domain = "data.linz.govt.nz"
        self.api_key_instance = self.ldi.api_key_instance
        self.api_key_instance.setApiKeys({domain: API_KEYS[domain]})

        # Test data dir and plugin settigns dir
        self.test_dir = os.path.dirname(os.path.realpath(__file__))
        self.test_data_dir = os.path.join(self.test_dir, "data")
        self.pl_settings_dir = os.path.join(
            QgsApplication.qgisSettingsDirPath(), "linz-data-importer"
        )

        # Delete all service xml files in plugin settigns dir
        os.chdir(self.pl_settings_dir)
        cache_files = glob.glob("*_*_[0-9]*.xml")
        for file in cache_files:
            os.remove(os.path.join(self.pl_settings_dir, file))

        # Copy in /test/data service xml to save time if they exist.
        # In most cases they dont as I can not make available with API Key
        # via github. If these are not avilable wfs will be fetch for data portal
        os.chdir(self.test_data_dir)

        test_files = glob.glob("data.linz.govt.nz_*_[0-9]*.xml")
        for file in test_files:
            file = os.path.join(self.test_data_dir, file)
            # if os.path.exists(file):
            shutil.copy(file, self.pl_settings_dir)

        # Copy in corrupt file for the test
        try:
            os.chdir(self.pl_settings_dir)
            wmts_file = glob.glob("data.linz.govt.nz_wmts_*.xml")
            wmts_file = os.path.join(self.pl_settings_dir, wmts_file[0])
            os.remove(wmts_file)
        except:
            pass
        corr_file_name = "data.linz.govt.nz_wmts_corrupt.xml"
        corr_file = os.path.join(self.test_data_dir, corr_file_name)  # src
        shutil.copy(corr_file, self.pl_settings_dir)

        # Rename
        new_corr_file = os.path.join(self.pl_settings_dir, corr_file_name)
        name_file_to = os.path.join(
            self.pl_settings_dir, corr_file_name.replace("_corrupt", "_20181025141022")
        )
        os.rename(new_corr_file, name_file_to)
        QTest.qWait(WAIT)

    def tearDown(self):
        """Runs after each test"""
        QTest.qWait(WAIT)
        self.ldi.dlg.uTextFilter.setText("")
        self.ldi.dlg.close()
        self.services_loaded = False

    def test_handle_corrupt_xml(self):
        """
        Setup has
        1. placed  corrupt file in the cache

        Test
        1. Test file is corrupt
        1. Runs plug
        2. Test file is not corrupt
        """

        # Test file is corrupt
        os.chdir(self.pl_settings_dir)
        cpt_file = glob.glob("data.linz.govt.nz_wmts_[0-9]*.xml")[0]
        cpt_file = os.path.join(self.pl_settings_dir, cpt_file)
        is_corrupt = False
        try:
            ET.parse(cpt_file)
        except ET.ParseError:
            is_corrupt = True
        self.assertTrue(is_corrupt)
        # Run Plugin
        self.ldi.services_loaded = False
        self.ldi.actions[0].trigger()
        QTest.qWait(1000)
        # ensure all services are are present in the table
        data_types = set(
            [
                self.ldi.proxy_model.index(row, 2).data()
                for row in range(self.ldi.proxy_model.rowCount())
            ]
        )
        self.assertEqual(len(data_types), 2)
        self.assertEqual(sorted([u"WFS", u"WMTS"]), sorted(list(data_types)))

class cacheTest(unittest.TestCase):
    """
    Test method for clearing old files from cache
    """

    def setUp(self):
        # 1. create six files
        # 2. three suffixed with one date three with the other
        # 3. Run the purge. Should only be the newest left.
        self.ldi = plugins.get("linz-data-importer")
        self.pl_settings_dir = os.path.join(
            QgsApplication.qgisSettingsDirPath(), "linz-data-importer"
        )

        self.old_file1 = "data.govt.test.nz_wfs_000000000000001.xml"
        self.old_file2 = "data.govt.test.nz_wfs_000000000000003.xml"
        self.new_file = "data.govt.test.nz_wfs_999999999999999.xml"
        self.test_files = [self.old_file1, self.old_file2, self.new_file]

        for file in self.test_files:
            with open(file, "w") as f:
                f.write("")

    def tearDown(self):
        """Runs after each test"""

        for file in self.test_files:
            try:
                os.remove(file)
            except:
                pass

    def test_purgeCache(self):
        """
        Test the purge removes the old files leaving
        just the most current
        """

        os.chdir(self.pl_settings_dir)
        pre_purge_test_files = glob.glob("data.govt.test.nz_wfs_[0-9]*.xml")
        self.assertEqual(sorted(pre_purge_test_files), sorted(self.test_files))
        self.ldi.local_store.purgeCache()
        post_purge_test_files = glob.glob("data.govt.test.nz_wfs_[0-9]*.xml")
        self.assertEqual(
            post_purge_test_files, ["data.govt.test.nz_wfs_999999999999999.xml"]
        )


class UserWorkFlows(unittest.TestCase):
    """
    Test user work flows to import data via the plugin
    """

    @classmethod
    def setUpClass(cls):
        """
        Set up at TestCase init
        """

        # Get the test executors current key so that
        # We can revert back to when tests are complete
        cls.testers_keys = QSettings().value("linz_data_importer/apikeys")

    @classmethod
    def tearDownClass(cls):
        """
        Clean up at TestCase teardown
        """

        # Runs at TestCase teardown.
        QSettings().setValue("linz_data_importer/apikeys", cls.testers_keys)

    def setUp(self):
        """
        Runs before each test
        """

        self.ldi = plugins.get("linz-data-importer")
        self.ldi.update_cache = False
        self.ldi.services_loaded = False

        self.api_key_instance = self.ldi.api_key_instance
        keys = {key: API_KEYS[key] for key in API_KEYS.keys() 
                               & {'data.linz.govt.nz', 'basemaps.linz.govt.nz'}}
        self.api_key_instance.setApiKeys(keys)


        self.ldi.selected_crs = "ESPG:2193"
        self.ldi.selected_crs_int = 2193

        # Run
        self.ldi.actions[0].trigger()

    def tearDown(self):
        """
        Runs after each test
        """

        QTest.qWait(WAIT)  # Just because I want to watch it open a close
        self.ldi.dlg.uTextFilter.setText("")
        self.ldi.dlg.close()
        QgsProject.instance().removeAllMapLayers()
        self.services_loaded = False
        item = self.ldi.dlg.uListOptions.findItems("ALL", Qt.MatchFixedString)[0]
        self.ldi.dlg.uListOptions.itemClicked.emit(item)

    def test_wfs_import(self):
        """
        Test display, filtering, selection and importing of WFS data
        """

        self.import_service("wfs")

    def test_wmts_import(self):
        """
        Test display, filtering, selection and importing of WFS data
        """

        self.import_service("wmts")

    def import_service(self, service):
        """
        Executes tests for all "test_w<x>s_import" methods
        """

        # Select WxS table view
        item = self.ldi.dlg.uListOptions.findItems(
            service.upper(), Qt.MatchFixedString
        )[0]
        self.ldi.dlg.uListOptions.itemClicked.emit(item)

        # Test the tableview widget is current stackedWidget
        self.assertEqual(self.ldi.dlg.uStackedWidget.currentIndex(), 0)

        # Test there is data
        self.assertNotEqual(self.ldi.table_model.rowCount(None), 0)

        # Test there is no error
        self.assertEqual(self.ldi.dlg.uLabelWarning.text(), '')

        # Ensure all records are of the selected type
        data_types = set(
            [
                self.ldi.proxy_model.index(row, 2).data()
                for row in range(self.ldi.proxy_model.rowCount())
            ]
        )
        self.assertEqual(len(data_types), 1)
        self.assertEqual(service.upper(), list(data_types)[0])

        nconfs = len(TEST_CONF[service])
        for i in range(nconfs):

          layerName = TEST_CONF[service][i]

          # Filter
          self.ldi.dlg.uTextFilter.setText(layerName)
          QTest.qWait(WAIT)

          # Check we have a single row in the view, upon filtering
          self.assertEquals(self.ldi.proxy_model.rowCount(), 1)

          # Import the first row
          self.ldi.dlg.uTableView.selectRow(0)
          self.ldi.dlg.uBtnImport.clicked.emit(True)

        names = [layer.name() for layer in QgsProject.instance().mapLayers().values()]
        self.assertEqual(len(names), nconfs)

        # Test the LayerRegistry to ensure all the layers have been imported
        self.assertEqual(set(names), set(TEST_CONF[service]))

    def test_all_services(self):
        """
        Test all services are shown in table
        """

        # Set up
        item = self.ldi.dlg.uListOptions.findItems("ALL", Qt.MatchFixedString)[0]
        self.ldi.dlg.uListOptions.itemClicked.emit(item)
        # Tests
        # Test there is data
        self.assertNotEqual(self.ldi.table_model.rowCount(None), 0)
        # ensure all services are are present in the table
        data_types = set(
            [
                self.ldi.proxy_model.index(row, 2).data()
                for row in range(self.ldi.proxy_model.rowCount())
            ]
        )
        self.assertEqual(len(data_types), 2)
        self.assertEqual(sorted([u"WFS", u"WMTS"]), sorted(list(data_types)))


# def suite():
#     suite = unittest.TestSuite()
#     suite.addTests(unittest.makeSuite(ApiKeyTest, 'test'))
#     return suite
#
# def run_tests():
#     unittest.TextTestRunner(verbosity=3).run(suite())
