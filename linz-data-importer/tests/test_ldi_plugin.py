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

import glob
import os
import re
import shutil
import unittest

from qgis.core import QgsApplication, QgsProject  # pylint:disable=import-error
from qgis.PyQt.QtCore import QSettings  # pylint:disable=import-error
from qgis.PyQt.QtTest import QTest  # pylint:disable=import-error
from qgis.utils import plugins  # pylint:disable=import-error

WAIT = 1000

# Must have the below envi vars set
API_KEYS = {
    "data.linz.govt.nz": os.getenv("LDI_LINZ_KEY", None),
    "data.mfe.govt.nz": os.getenv("LDI_MFE_KEY", None),
    "geodata.nzdf.mil.nz": os.getenv("LDI_NZDF_KEY", None),
}


class UnitLevel(unittest.TestCase):
    """Testing smallest units  against
    live QGIS instance rather than mocking"""

    @classmethod
    def setUpClass(cls):
        #         """Runs at TestCase init."""
        # Get the test executors current key so that
        # We can revert back to when tests are complete
        cls.testers_keys = QSettings().value("linz_data_importer/apikeys")

    @classmethod
    def tearDownClass(cls):
        # Runs at TestCase teardown.
        QSettings().setValue("linz_data_importer/apikeys", cls.testers_keys)

    def copy_test_data(self):
        """
        Copy test data from ./test/data to plugin settings dir.
        This makes tests run much faster than having to fetch the resources
        from the internet repeatability

        Not available with CI (due to API Keys in file)
        """

        # test files not available to CI (apikeys within)

        # But locally using test/data xml for reading is much faster
        # as the plugin will not go out to the internet (if update_cache=False)
        self.test_dir = os.path.dirname(os.path.realpath(__file__))
        self.test_data_dir = os.path.join(self.test_dir, "data")
        self.pl_settings_dir = os.path.join(
            QgsApplication.qgisSettingsDirPath(), "linz-data-importer"
        )
        # delete all service xml files
        search_str = "|".join(["_{}.xml".format(x) for x in ["wfs", "wmts"]])
        for settings_filename in os.listdir(self.pl_settings_dir):
            if re.search(search_str, settings_filename):
                os.remove(os.path.join(self.pl_settings_dir, settings_filename))

        # Copy in /test/data service xml to save time.
        for data_filename in os.listdir(self.test_data_dir):
            if re.search(search_str, data_filename):
                file = os.path.join(self.test_data_dir, data_filename)
                shutil.copy(file, self.pl_settings_dir)

    def setUp(self):
        """
        Runs before each test
        """

        self.domain1 = "data.mfe.govt.nz"
        self.domain2 = "data.linz.govt.nz"
        self.copy_test_data()

        self.ldi = plugins.get("linz-data-importer")
        self.ldi.selection_model.blockSignals(True)
        self.api_key_instance = self.ldi.api_key_instance
        self.api_key_instance.set_api_keys({self.domain1: API_KEYS[self.domain1]})
        self.ldi.load_settings()
        self.ldi.update_cache = False
        self.ldi.services_loaded = True
        # Run
        self.ldi.actions[0].trigger()

    def tearDown(self):
        """
        Runs after each test
        """

        QTest.qWait(WAIT)  # Just because I want to watch it open and close
        self.ldi.dlg.uTextFilter.setText("")
        self.ldi.dlg.close()
        QgsProject.instance().removeAllMapLayers()
        self.ldi.clear_settings()
        self.ldi.wmts_epsg = "EPSG:3857"
        self.ldi.selection_model.blockSignals(False)

    def test_clear_settings(self):
        """
        Test the text is cleared from the setting tab QLineEdits
        """

        # Unit test setup
        # And text to settings qLineEdits
        for entry in range(1, 3):
            getattr(self.ldi.dlg, "uTextDomain{0}".format(entry)).setText(
                "test{0}".format(entry)
            )
            getattr(self.ldi.dlg, "uTextAPIKey{0}".format(entry)).setText(
                "test{0}".format(entry)
            )
        # Check the text is there
        for entry in range(1, 3):
            self.assertEqual(
                getattr(self.ldi.dlg, "uTextDomain{0}".format(entry)).text(),
                "test{0}".format(entry),
            )
            self.assertEqual(
                getattr(self.ldi.dlg, "uTextAPIKey{0}".format(entry)).text(),
                "test{0}".format(entry),
            )
        # Run the method we are testing
        self.ldi.clear_settings()
        # did it work?
        for entry in range(1, 3):
            self.assertEqual(
                getattr(self.ldi.dlg, "uTextDomain{0}".format(entry)).text(), ""
            )
            self.assertEqual(
                getattr(self.ldi.dlg, "uTextAPIKey{0}".format(entry)).text(), ""
            )

    def test_load_settings(self):
        """
        Test Settings are loaded to the Settings Tab QLineEdits
        """

        # setup is loading settings so...
        self.ldi.clear_settings()
        # confirm pre test state is as expected
        for entry in range(1, 11):
            self.assertEqual(
                getattr(self.ldi.dlg, "uTextDomain{0}".format(entry)).text(), ""
            )
            self.assertEqual(
                getattr(self.ldi.dlg, "uTextAPIKey{0}".format(entry)).text(), ""
            )
        # Run the method we are testing
        self.ldi.load_settings()
        # The api keys and domain set in setup should be present in the ui
        self.assertEqual(self.ldi.dlg.uTextDomain1.text(), self.domain1)
        self.assertEqual(self.ldi.dlg.uTextAPIKey1.text(), API_KEYS[self.domain1])

    def test_save_domain_save(self):
        """
        Test the entering and saving of settings
        """
        return True  # TEMP DEBUGGING
        # Really an int test. Main thing we need to see
        # is the apikey QSettings update.

        # confirm pre test state is as expected
        # pylint:disable=unreachable
        self.assertEqual(
            {self.domain1: API_KEYS[self.domain1]}, self.api_key_instance.get_api_keys()
        )
        self.ldi.load_settings()
        self.assertEqual(self.ldi.dlg.uTextDomain1.text(), self.domain1)
        self.assertEqual(self.ldi.dlg.uTextAPIKey1.text(), API_KEYS[self.domain1])

        # add the details to the ui that will be saved.
        self.ldi.dlg.uTextDomain2.setText(self.domain2)
        self.ldi.dlg.uTextAPIKey2.setText(API_KEYS[self.domain2])

        # Run the method we are testing - must be called from btn clicked
        self.ldi.dlg.uBtnSaveDomain2.clicked.emit(True)
        # The 2nd api key and domain should be set and present in the ui
        api_keys = {
            self.domain1: API_KEYS[self.domain1],
            self.domain2: API_KEYS[self.domain2],
        }
        self.assertEqual(api_keys, self.api_key_instance.get_api_keys())
        curr_keys = {
            self.ldi.dlg.uTextDomain1.text(): self.ldi.dlg.uTextAPIKey1.text(),
            self.ldi.dlg.uTextDomain2.text(): self.ldi.dlg.uTextAPIKey2.text(),
        }

        self.assertEqual(
            curr_keys,
            {
                self.domain1: API_KEYS[self.domain1],
                self.domain2: API_KEYS[self.domain2],
            },
        )

    def test_save_domain_remove(self):
        """
        Test the removal of a settings record.
        """

        # confirm pre test state is as expected
        self.assertEqual(
            {self.domain1: API_KEYS[self.domain1]}, self.api_key_instance.get_api_keys()
        )
        self.ldi.load_settings()
        self.assertEqual(self.ldi.dlg.uTextDomain1.text(), self.domain1)
        self.assertEqual(self.ldi.dlg.uTextAPIKey1.text(), API_KEYS[self.domain1])
        # Run the method we are testing - must be called from btn clicked
        self.ldi.dlg.uBtnRemoveDomain1.clicked.emit(True)
        # Check the record has been removed from the api settings property
        self.assertEqual({}, self.api_key_instance.get_api_keys())

    def test_add_new_domain(self):
        """
        Test UI functionality for adding new settings details
        """

        idx = self.ldi.dlg.uComboBoxDomain.findText(self.domain2)
        self.ldi.dlg.uComboBoxDomain.setCurrentIndex(idx)
        self.assertEqual(self.ldi.dlg.uComboBoxDomain.currentText(), self.domain2)
        # Test the method
        self.ldi.dlg.uBtnAddDomain.clicked.emit(True)
        QTest.qWait(2000)
        self.assertEqual(self.ldi.dlg.uTextDomain2.text(), self.domain2)
        # Other rows should be hidden
        for entry in range(3, 11):
            self.assertFalse(
                getattr(self.ldi.dlg, "uTextDomain{0}".format(entry)).isVisible()
            )
            self.assertFalse(
                getattr(self.ldi.dlg, "uTextAPIKey{0}".format(entry)).isVisible()
            )

    def test_add_new_domain_duplicate(self):
        """
        Test case where by the user tries to add duplicate domain details
        """

        idx = self.ldi.dlg.uComboBoxDomain.findText(self.domain1)
        self.ldi.dlg.uComboBoxDomain.setCurrentIndex(idx)
        # Test the method
        self.ldi.dlg.uBtnAddDomain.clicked.emit(True)
        # First as we are selecting a domian that already exists
        # this should show a warning
        #         self.assertTrue(self.ldi.dlg.uWarningSettings.isVisible())
        self.assertTrue(
            self.ldi.dlg.uWarningSettings.text(),
            "Warning: Domains must be unique. " "Please edit the domain below",
        )

    def test_add_new_domain_lessthan_max_entires(self):
        """
        Test no warnings are shown when not exceeding max settings entries
        """

        self.api_key_instance.set_api_keys(
            {
                "1": "1",
                "2": "2",
                "3": "3",
                "4": "4",
                "5": "5",
                "6": "6",
                "7": "7",
                "8": "8",
                "9": "9",
            }
        )
        self.ldi.load_settings()
        idx = self.ldi.dlg.uComboBoxDomain.findText(self.domain1)
        self.ldi.dlg.uComboBoxDomain.setCurrentIndex(idx)
        # Test the method
        self.ldi.dlg.uBtnAddDomain.clicked.emit(True)
        # First as we are selecting a domian that already exists
        # this should show a warning
        #         self.assertTrue(self.ldi.dlg.uWarningSettings.isVisible())
        self.assertTrue(self.ldi.dlg.uWarningSettings.text(), "")

    def test_add_new_domain_greaterthan_max_entires(self):
        """
        Test warning is shown when exceeding max number of settings entries
        """

        self.api_key_instance.set_api_keys(
            {
                "1": "1",
                "2": "2",
                "3": "3",
                "4": "4",
                "5": "5",
                "6": "6",
                "7": "7",
                "8": "8",
                "9": "9",
                "10": "10",
            }
        )
        self.ldi.load_settings()
        idx = self.ldi.dlg.uComboBoxDomain.findText(self.domain1)
        self.ldi.dlg.uComboBoxDomain.setCurrentIndex(idx)
        # Test the method
        self.ldi.dlg.uBtnAddDomain.clicked.emit(True)
        # First as we are selecting a domian that already exists
        # this should show a warning
        #         self.assertTrue(self.ldi.dlg.uWarningSettings.isVisible())
        self.assertTrue(
            self.ldi.dlg.uWarningSettings.text(),
            "Warning: You can only store up to . " "10 domain entries",
        )

    def test_update_service_data_cache(self):
        """
        Test the updating of cache
        """

        self.ldi.services_loaded = False
        self.ldi.run()

        insitu_file_stats = {}
        cached_file_stats = {}

        os.chdir(self.pl_settings_dir)
        for service in ["wfs", "wmts"]:
            files = glob.glob("{0}_{1}*.xml".format(self.domain1, service))
            file = files[-1]
            file_path = os.path.join(self.pl_settings_dir, file)
            insitu_file_stats[file] = os.stat(file_path).st_mtime

        self.ldi.cache_updated = False
        self.ldi.update_cache = True
        self.ldi.update_service_data_cache()
        QTest.qWait(15000)

        for service in ["wfs", "wmts"]:
            files = glob.glob("{0}_{1}*.xml".format(self.domain1, service))
            file = files[-1]
            file_path = os.path.join(self.pl_settings_dir, file)
            cached_file_stats[file] = os.stat(file_path).st_mtime
        self.assertNotEqual(cached_file_stats, insitu_file_stats)

    def test_set_project_srid(self):
        """
        Test the setting of the projects crs
        """

        # Get plugins default srs
        test_srid_int = 3793
        # Test current state
        self.assertNotEqual(self.ldi.map_crs(), test_srid_int)

        # Change srid via method
        self.ldi.selected_crs_int = test_srid_int
        self.ldi.set_project_srid()
        # Test method
        self.assertEqual(self.ldi.map_crs().lstrip("EPSG:"), str(test_srid_int))

    @unittest.skip(
        "Intermittent 'IndexError: list index out of range' when running `names[0]`"
    )
    def test_import_dataset_wfs(self):
        """
        Test the importing of WFS layers into QGIS
        """

        # set plugin properties required for import
        self.ldi.domain = self.domain1  # mfe
        self.ldi.service = "WFS"
        self.ldi.data_type = "layer"
        self.ldi.object_id = "53318"
        self.ldi.layer_title = "test_wfs"
        self.ldi.selected_crs = "ESPG:2193"
        self.ldi.selected_crs_int = 2193
        self.ldi.import_dataset()
        # test the layer has been imported
        names = [layer.name() for layer in QgsProject.instance().mapLayers().values()]
        self.assertEqual(self.ldi.layer_title, names[0])

    def test_import_dataset_wmts(self):
        """
        Test the importing of WMTS layers into QGIS
        """

        # set plugin properties required for import
        self.api_key_instance.set_api_keys({self.domain2: API_KEYS[self.domain2]})
        self.ldi.domain = self.domain2  # linz
        self.ldi.service = "WMTS"
        self.ldi.data_type = "layer"
        self.ldi.object_id = "51320"
        self.ldi.layer_title = "test_wmts"
        self.ldi.selected_crs = "EPSG:3857"
        self.ldi.selected_crs_int = 3857
        self.ldi.import_dataset()
        # test the layer has been imported
        names = [layer.name() for layer in QgsProject.instance().mapLayers().values()]
        self.assertEqual(self.ldi.layer_title, names[0])


def suite():
    test_suite = unittest.TestSuite()
    test_suite.addTests(unittest.makeSuite(UnitLevel, "test"))
    return test_suite


def run_tests():
    unittest.TextTestRunner(verbosity=3).run(suite())
