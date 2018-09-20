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
import ast
import os
import shutil
import re
import io

from PyQt4.QtTest import QTest
from qgis.PyQt.QtCore import Qt, QSettings, QBuffer
from qgis.PyQt.QtGui import QImage
from qgis.utils import plugins
from qgis.core import QgsMapLayerRegistry, QgsApplication

WAIT=1000
API_KEYS=ast.literal_eval(os.getenv('LDS_PLUGIN_API_KEYS', None))

class UnitLevel(unittest.TestCase):
    """ Testing smallest units  against
    live QGIS instance rather than mocking """

    @classmethod
    def setUpClass(cls):
#         """Runs at TestCase init."""
        # Get the test executors current key so that 
        # We can revert back to when tests are complete
        cls.testers_keys = QSettings().value('ldsplugin/apikeys')

    @classmethod
    def tearDownClass(cls):
        # Runs at TestCase teardown.
        QSettings().setValue('ldsplugin/apikey', cls.testers_keys)

    def copyTestData(self):
        """
        Copy test data from ./test/data to plugin settings dir. 
        This makes tests run much faster than having to fetch the resources
        from the internet repeatability 

        Not available with CI (due to API Keys in file)
        """

        # test files not available to CI (apikeys within)

        # But locally using test/data xml for reading is much faster
        # as the plugin will not go out to the internet (if update_cache=False) 
        self.test_dir=os.path.dirname(os.path.realpath(__file__))
        self.test_data_dir=os.path.join(self.test_dir, 'data')
        self.pl_settings_dir=os.path.join(QgsApplication.qgisSettingsDirPath(), "ldsplugin")
        #delete all service xml files
        search_str = '|'.join(['_{}.xml'.format(x) for x in ['wms','wfs','wmts']])
        for f in os.listdir(self.pl_settings_dir):
            if re.search(search_str, f):
                os.remove(os.path.join(self.pl_settings_dir, f))

        # Copy in /test/data service xml to save time.
        for f in os.listdir(self.test_data_dir):
            if re.search(search_str, f):
                file=os.path.join(self.test_data_dir, f)
                shutil.copy(file, self.pl_settings_dir)

    def setUp(self):
        """
        Runs before each test
        """

        self.domain1='data.mfe.govt.nz'
        self.domain2='data.linz.govt.nz'
        self.copyTestData()

        self.lds_plugin = plugins.get('ldsplugin')
        self.dlg=self.lds_plugin.service_dlg
        self.api_key_instance = self.lds_plugin.api_key_instance
        self.api_key_instance.setApiKeys({self.domain1:API_KEYS[self.domain1]})
        self.lds_plugin.loadSettings()
        self.lds_plugin.update_cache=False
        # Run
        self.lds_plugin.actions[0].trigger()

    def tearDown(self):
        """
        Runs after each test
        """

        QTest.qWait(WAIT) # Just because I want to watch it open and close
        self.dlg.uTextFilter.setText('')
        self.dlg.close()
        QgsMapLayerRegistry.instance().removeAllMapLayers()
        self.services_loaded=False
        self.cache_updated=False
        self.lds_plugin.clearSettings()
        self.lds_plugin.wmts_epsg="EPSG:3857"
        self.lds_plugin.canvas.setCrsTransformEnabled(False)
        self.lds_plugin.cache_updated=False

    def test_clearSettings(self):
        """
        Test the text is cleared from the setting tab QLineEdits
        """

        # Unit test setup
        # And text to settings qLineEdits
        for n in range(1,3):
            getattr(self.dlg, 'uTextDomain{0}'.format(n)).setText('test{0}'.format(n))
            getattr(self.dlg, 'uTextAPIKey{0}'.format(n)).setText('test{0}'.format(n))
        # Check the text is there
        for n in range(1,3):
            self.assertEqual(getattr(self.dlg, 'uTextDomain{0}'.format(n)).text(), 'test{0}'.format(n))
            self.assertEqual(getattr(self.dlg, 'uTextAPIKey{0}'.format(n)).text(), 'test{0}'.format(n))
        # Run the method we are testing
        self.lds_plugin.clearSettings()
        #did it work?
        for n in range(1,3):
            self.assertEqual(getattr(self.dlg, 'uTextDomain{0}'.format(n)).text(), '')
            self.assertEqual(getattr(self.dlg, 'uTextAPIKey{0}'.format(n)).text(), '')

    def test_loadSettings(self):
        """
        Test Settings are loaded to the Settings Tab QLineEdits
        """

        #setup is loading settings so...
        self.lds_plugin.clearSettings()
        # confirm pre test state is as expected
        for n in range(1,11):
            self.assertEqual(getattr(self.dlg, 'uTextDomain{0}'.format(n)).text(), '')
            self.assertEqual(getattr(self.dlg, 'uTextAPIKey{0}'.format(n)).text(), '')
        # Run the method we are testing
        self.lds_plugin.loadSettings()
        # The api keys and domain set in setup should be present in the ui
        self.assertEqual(self.dlg.uTextDomain1.text(), self.domain1)
        self.assertEqual(self.dlg.uTextAPIKey1.text(), API_KEYS[self.domain1])

    def test_saveDomain_save(self):
        """
        Test the entering and saving of settings
        """

        # Really an int test. Main thing we need to see
        # is the apikey QSettings update.

        # confirm pre test state is as expected
        self.assertEqual({self.domain1:API_KEYS[self.domain1]}, self.api_key_instance.getApiKeys())
        self.lds_plugin.loadSettings()
        self.assertEqual(self.dlg.uTextDomain1.text(), self.domain1)
        self.assertEqual(self.dlg.uTextAPIKey1.text(), API_KEYS[self.domain1])

        # add the details to the ui that will be saved. 
        self.dlg.uTextDomain2.setText(self.domain2)
        self.dlg.uTextAPIKey2.setText(API_KEYS[self.domain2])
        # Run the method we are testing - must be called from btn clicked
        self.dlg.uBtnSaveDomain2.clicked.emit(True)
        # The 2nd api key and domain should be set and present in the ui
        api_keys={self.domain1:API_KEYS[self.domain1], self.domain2:API_KEYS[self.domain2]}
        self.assertEqual(api_keys, self.api_key_instance.getApiKeys())
        curr_keys={self.dlg.uTextDomain1.text():self.dlg.uTextAPIKey1.text(),
                   self.dlg.uTextDomain2.text():self.dlg.uTextAPIKey2.text()}

        self.assertEqual(curr_keys, {self.domain1:API_KEYS[self.domain1],
                                     self.domain2:API_KEYS[self.domain2]})

    def test_saveDomain_remove(self):
        """
        Test the removal of a settings record. 
        """

        # confirm pre test state is as expected
        self.assertEqual({self.domain1:API_KEYS[self.domain1]}, self.api_key_instance.getApiKeys())
        self.lds_plugin.loadSettings()
        self.assertEqual(self.dlg.uTextDomain1.text(), self.domain1)
        self.assertEqual(self.dlg.uTextAPIKey1.text(), API_KEYS[self.domain1])
        # Run the method we are testing - must be called from btn clicked
        self.dlg.uBtnRemoveDomain1.clicked.emit(True)
        # Check the record has been removed from the api settings property 
        self.assertEqual({}, self.api_key_instance.getApiKeys())

    def test_addNewDomain(self):
        """
        Test UI functionality for adding new settings details 
        """

        idx=self.dlg.uComboBoxDomain.findText(self.domain2)
        self.dlg.uComboBoxDomain.setCurrentIndex(idx)
        self.assertEqual(self.dlg.uComboBoxDomain.currentText(), self.domain2)
        # Test the method
        self.dlg.uBtnAddDomain.clicked.emit(True)
        QTest.qWait(2000)
        self.assertEqual(self.dlg.uTextDomain2.text(), self.domain2)
        # Other rows should be hidden
        for n in range(3,11):
            self.assertFalse(getattr(self.dlg, 'uTextDomain{0}'.format(n)).isVisible())
            self.assertFalse(getattr(self.dlg, 'uTextAPIKey{0}'.format(n)).isVisible())

    def test_addNewDomain_duplicate(self):
        """
        Test case where by the user tries to add duplicate domain details
        """

        idx=self.dlg.uComboBoxDomain.findText(self.domain1)
        self.dlg.uComboBoxDomain.setCurrentIndex(idx)
        # Test the method
        self.dlg.uBtnAddDomain.clicked.emit(True)
        # First as we are selecting a domian that already exists
        # this should show a warning
#         self.assertTrue(self.dlg.uWarningSettings.isVisible())
        self.assertTrue(self.dlg.uWarningSettings.text(), 
                        'Warning: Domains must be unique. '
                        'Please edit the domain below')

    def test_addNewDomain_lessthan_max_entires(self):
        """
        Test no warnings are shown when not exceeding max settings entries 
        """

        self.api_key_instance.setApiKeys({'1':'1',
                                          '2':'2',
                                          '3':'3',
                                          '4':'4',
                                          '5':'5',
                                          '6':'6',
                                          '7':'7',
                                          '8':'8',
                                          '9':'9',
                                          })
        self.lds_plugin.loadSettings()
        idx=self.dlg.uComboBoxDomain.findText(self.domain1)
        self.dlg.uComboBoxDomain.setCurrentIndex(idx)
        # Test the method
        self.dlg.uBtnAddDomain.clicked.emit(True)
        # First as we are selecting a domian that already exists
        # this should show a warning
#         self.assertTrue(self.dlg.uWarningSettings.isVisible())
        self.assertTrue(self.dlg.uWarningSettings.text(), '')

    def test_addNewDomain_greaterthan_max_entires(self):
        """
        Test warning is shown when exceeding max number of settings entries 
        """

        self.api_key_instance.setApiKeys({'1':'1',
                                          '2':'2',
                                          '3':'3',
                                          '4':'4',
                                          '5':'5',
                                          '6':'6',
                                          '7':'7',
                                          '8':'8',
                                          '9':'9',
                                          '10':'10'})
        self.lds_plugin.loadSettings()
        idx=self.dlg.uComboBoxDomain.findText(self.domain1)
        self.dlg.uComboBoxDomain.setCurrentIndex(idx)
        # Test the method
        self.dlg.uBtnAddDomain.clicked.emit(True)
        # First as we are selecting a domian that already exists
        # this should show a warning
#         self.assertTrue(self.dlg.uWarningSettings.isVisible())
        self.assertTrue(self.dlg.uWarningSettings.text(), 'Warning: You can only store up to . '
                                                      '10 domain entries')

    def test_unload(self):
        """
        Not Currently Tested
        """
        # Run unload check icon has been removed

        pass

    def test_run(self):
        """
        Test via int tests 
        """

        pass

    def test_run_warning(self):
        """
        Test via int tests 
        """

        pass

    def test_updateServiceDataCache(self):
        """
        Test the updating of cache
        """

        insitu_file_stats={}
        cached_file_stats={}

        for service in ['wms','wfs','wmts']:
            file='{0}_{1}.xml'.format(self.domain1,service)
            file_path=os.path.join(self.pl_settings_dir, file)
            insitu_file_stats[file]=os.stat(file_path).st_mtime

        self.lds_plugin.services_loaded=True
        self.lds_plugin.updateServiceDataCache()
        while not self.lds_plugin.cache_updated:
            QTest.qWait(5000)

        for service in ['wms','wfs','wmts']:
            file='{0}_{1}.xml'.format(self.domain1,service)
            file_path=os.path.join(self.pl_settings_dir, file)
            QTest.qWait(5000)
            cached_file_stats[file]=os.stat(file_path).st_mtime
        self.assertNotEqual(cached_file_stats, insitu_file_stats)

    def test_loadUi(self):
        """ 
        Test via int tests 
        """
        pass

    def test_loadAllServices(self):
        """ 
        Test via int tests 
        """
        pass

    def test_dataToTable(self):
        """ 
        Test via int tests 
        """
        pass

    def test_showSelectedOption(self):
        """ 
        Test via int tests 
        """
        pass

    def test_getPreview(self):
        """
        Test the getting of a preview image
        """

        match_layer_id=53309
        mismatch_layer_id=53158
        self.lds_plugin.id=match_layer_id
        self.lds_plugin.getPreview('300x200', 10)
        test_image1=os.path.join(self.test_data_dir,str(match_layer_id)+'.png')
        test_image2=os.path.join(self.test_data_dir,str(mismatch_layer_id)+'.png')

        preview_img=self.lds_plugin.qimage

        test_img_match = QImage(test_image1) #should match
        test_img_mismatch = QImage(test_image2) #shouldn't match

        bytes_preview=preview_img.bits().asstring(preview_img.numBytes())
        bytes_match=test_img_match.bits().asstring(test_img_match.numBytes())
        bytes_mismatch=test_img_mismatch.bits().asstring(test_img_mismatch.numBytes())
        # Is the downloaded image the as the stored?  
        self.assertEqual(bytes_match, bytes_preview)
        self.assertNotEqual(bytes_mismatch, bytes_preview)

    def test_updDescription(self):
        """ 
        Test via int tests 
        """
        pass

    def test_updPreview(self):
        """ 
        Test via int tests 
        """
        pass

    def test_filterTable(self):
        """ 
        Test via int tests 
        """
        pass

    def test_mapCrs(self):
        """ 
        Test via int tests 
        """
        pass

    def test_enableOTF(self):
        """
        Test enabling QGIS's OTF
        """
        # test current state
        otf=self.lds_plugin.canvas.hasCrsTransformEnabled()
        self.assertFalse(otf)
        # Run the mthod
        self.lds_plugin.enableOTF()
        otf=self.lds_plugin.canvas.hasCrsTransformEnabled()
        self.assertTrue(otf)

    def test_setSRID(self):
        """
        Test the setting of the projects crs
        """

        # Get plugins default srs 
        default_srid=self.lds_plugin.wmts_epsg.lstrip('EPSG:')
        test_srid_int=3793
        # Test current state
        self.assertNotEqual(self.lds_plugin.mapCrs(), test_srid_int)

        # Change srid via method
        self.lds_plugin.wmts_epsg_int=test_srid_int
        # Test method
        self.lds_plugin.setSRID()
        self.assertEqual(self.lds_plugin.mapCrs().lstrip('EPSG:'), str(test_srid_int))

    def test_infoCRS(self):
        """
        Not currently tested
        """
        pass

    def test_importDataset_wfs(self):
        """
        Test the importing of WFS layers into QGIS
        """

        # set plugin properties required for import
        self.lds_plugin.domain=self.domain1
        self.lds_plugin.service='WFS'
        self.lds_plugin.service_type='layer'
        self.lds_plugin.id='52759'
        title='test_wfs'
        self.lds_plugin.layer_title=title
        self.lds_plugin.importDataset()
        #test the layer has been imported
        names = [layer.name() for layer in QgsMapLayerRegistry.instance().mapLayers().values()]
        self.assertEqual(title, names[0])

    def test_importDataset_wmts(self):
        """
        Test the importing of WMTS layers into QGIS
        """

        # set plugin properties required for import
        self.api_key_instance.setApiKeys({self.domain2:API_KEYS[self.domain2]})
        self.lds_plugin.domain=self.domain2
        self.lds_plugin.service='WMTS'
        self.lds_plugin.service_type='layer'
        self.lds_plugin.id='51320'
        title='test_wmts'
        self.lds_plugin.layer_title=title
        self.lds_plugin.importDataset()
        #test the layer has been imported
        names = [layer.name() for layer in QgsMapLayerRegistry.instance().mapLayers().values()]
        self.assertEqual(title, names[0])

    def test_importDataset_wms(self):
        """
        Test the importing of WMS layers into QGIS
        """

        # set plugin properties required for import
        self.api_key_instance.setApiKeys({self.domain2:API_KEYS[self.domain2]})
        self.lds_plugin.domain=self.domain2
        self.lds_plugin.service='WMS'
        self.lds_plugin.service_type='layer'
        self.lds_plugin.id='51409'
        title='test_wms'
        self.lds_plugin.layer_title=title
        self.lds_plugin.importDataset()
        #test the layer has been imported
        names = [layer.name() for layer in QgsMapLayerRegistry.instance().mapLayers().values()]
        self.assertEqual(title, names[0])

def suite():
    suite = unittest.TestSuite()
    suite.addTests(unittest.makeSuite(UiTest, 'test'))
    return suite

def run_tests():
    unittest.TextTestRunner(verbosity=3).run(suite())
